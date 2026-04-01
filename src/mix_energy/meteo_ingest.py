
import requests
import pandas as pd
import loguru
try:
    from .gcp_utils import connect_to_bucket, upload_data_in_bucket
except ImportError:
    from gcp_utils import connect_to_bucket, upload_data_in_bucket

BASE_URL = "https://api.open-meteo.com/v1/forecast"
latitude_paris = 48.8534
longitude_paris = 2.3488
latitude_lyon = 45.7640
longitude_lyon = 4.8357
latitude_lille = 50.6292
longitude_lille = 3.0573
latitude_dijon = 47.3220
longitude_dijon = 5.0415
latitude_rennes = 48.1173
longitude_rennes = -1.6778
latitude_orleans = 47.9029
longitude_orleans = 1.9093
latitude_strasbourg = 48.5734
longitude_strasbourg = 7.7521
latitude_caen = 49.1829
longitude_caen = -0.3707
latitude_bordeaux = 44.8378
longitude_bordeaux = -0.5792
latitude_toulouse = 43.6047
longitude_toulouse = 1.4442
latitude_marseille = 43.2965
longitude_marseille = 5.3698
latitude_nantes = 47.2184
longitude_nantes = -1.5536

past_days = 10
forecast_days = 1

CITIES = {
    "paris": (latitude_paris, longitude_paris),
    "lyon": (latitude_lyon, longitude_lyon),
    "lille": (latitude_lille, longitude_lille),
    "dijon": (latitude_dijon, longitude_dijon),
    "rennes": (latitude_rennes, longitude_rennes),
    "orleans": (latitude_orleans, longitude_orleans),
    "strasbourg": (latitude_strasbourg, longitude_strasbourg),
    "caen": (latitude_caen, longitude_caen),
    "bordeaux": (latitude_bordeaux, longitude_bordeaux),
    "toulouse": (latitude_toulouse, longitude_toulouse),
    "marseille": (latitude_marseille, longitude_marseille),
    "nantes": (latitude_nantes, longitude_nantes),
}


def get_meteo_forecast(
    latitude: float, longitude: float, past_days: int, forecast_days: int
) -> dict:
    """
    Récupère les données météorologiques pour une localisation donnée.

    Args:
            latitude: Latitude de la localisation
            longitude: Longitude de la localisation
            past_days: Nombre de jours passés à récupérer
            forecast_days: Nombre de jours futurs à récupérer
    Returns:
            Dictionnaire JSON contenant les données météorologiques
    """
    url = f"{BASE_URL}"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,dew_point_2m,precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,weather_code,pressure_msl,surface_pressure,cloud_cover,evapotranspiration,vapour_pressure_deficit,wind_speed_10m,wind_direction_10m,wind_gusts_10m,soil_temperature_0cm,soil_temperature_6cm,soil_temperature_18cm,soil_temperature_54cm,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_moisture_27_to_81cm",
        "timezone": "Europe/Berlin",
        "past_days": past_days,
        "forecast_days": forecast_days,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        loguru.logger.error(
            f"Erreur lors de la récupération des données météorologiques: {e}"
        )
        return {}

    loguru.logger.info(f"URL: {response.url[:50]}...")
    return response.json()


def json_to_dataframe(meteo_data: dict) -> pd.DataFrame:
    """
    Transforme les données JSON météo en dataframe pandas.

    Args:
        meteo_data: Dictionnaire JSON retourné par l'API Open-Meteo

    Returns:
        pd.DataFrame avec les données météorologiques horaires
    """
    hourly_data = meteo_data.get("hourly", {})
    df = pd.DataFrame(hourly_data)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    return df


def save_meteo_to_csv(df: pd.DataFrame, city_name: str):
    """
    Enregistre les données météorologiques dans un fichier CSV.

    Args:
            df: DataFrame contenant les données météorologiques
            city_name: Nom de la ville pour laquelle les données sont enregistrées
    """

    import os
    dir_path = "data/meteo"
    os.makedirs(dir_path, exist_ok=True)
    file_path = f"{dir_path}/meteo_{city_name}.csv"
    df.to_csv(file_path, index=False)
    loguru.logger.info(f"Données météorologiques enregistrées dans {file_path}")

    # Upload to GCP bucket
    bucket = connect_to_bucket()
    if bucket is not None:
        with open(file_path, "r") as f:
            content = f.read()
            upload_data_in_bucket(bucket, content, f"meteo_{city_name}")
        loguru.logger.info(f"Fichier {file_path} uploadé dans le bucket GCP.")
    else:
        loguru.logger.error("Impossible de se connecter au bucket GCP pour l'upload.")


def run_ingestion() -> None:
    """Récupère les données météo de toutes les villes et les enregistre en CSV."""
    for city_name, (latitude, longitude) in CITIES.items():
        meteo_payload = get_meteo_forecast(
            latitude, longitude, past_days, forecast_days
        )
        df_meteo = json_to_dataframe(meteo_payload)
        save_meteo_to_csv(df_meteo, city_name)


if __name__ == "__main__":
    run_ingestion()