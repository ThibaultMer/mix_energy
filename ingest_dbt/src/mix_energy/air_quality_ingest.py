import calendar
import csv
import io
import os
import requests

from datetime import date
from mix_energy import get_logger
from mix_energy.gcp_utils import connect_to_bucket, upload_data_in_bucket

# URL de l'API ATMO France (API Qualité de l'air)
BASE_URL = "https://admindata.atmo-france.org/api/v2/data/indices/atmo"

CITIES = {
    "paris": {"insee_commune": "75056", "code_aasqa": 11},  # Île-de-France (Airparif)
    "lyon": {"insee_commune": "69123", "code_aasqa": 84},  # Auvergne-Rhône-Alpes
    "lille": {"insee_commune": "59350", "code_aasqa": 32},  # Hauts-de-France
    "dijon": {"insee_commune": "21231", "code_aasqa": 27},  # Bourgogne-Franche-Comté
    "rennes": {"insee_commune": "35238", "code_aasqa": 53},  # Bretagne
    "orleans": {"insee_commune": "45234", "code_aasqa": 24},  # Centre-Val de Loire
    "strasbourg": {"insee_commune": "67482", "code_aasqa": 44},  # Grand Est
    "caen": {"insee_commune": "14118", "code_aasqa": 28},  # Normandie
    "bordeaux": {"insee_commune": "33063", "code_aasqa": 75},  # Nouvelle-Aquitaine
    "toulouse": {"insee_commune": "31555", "code_aasqa": 76},  # Occitanie
    "marseille": {
        "insee_commune": "13055",
        "code_aasqa": 93,
    },  # Provence-Alpes-Côte d'Azur (AtmoSud)
    "nantes": {"insee_commune": "44109", "code_aasqa": 52},  # Pays de la Loire
}

log = get_logger()


def save_air_quality_to_bucket(features: list[dict], bucket) -> bool:
    """Convertit les features ATMO en CSV et les envoie dans le bucket GCP (mode local ou Airflow)."""
    if not features:
        log.info("Aucune donnée à sauvegarder.")
        return False

    csv_buffer = io.StringIO()
    headers = list(features[0]["properties"].keys())

    writer = csv.DictWriter(csv_buffer, fieldnames=headers)
    writer.writeheader()
    for feat in features:
        writer.writerow(feat["properties"])

    # Callback Airflow si défini
    upload_callback = globals().get("_air_quality_upload_callback", None)
    if upload_callback is not None:
        upload_callback(csv_buffer.getvalue(), "air_quality_daily")
        log.info("Données déposées dans le bucket GCP (Airflow mode).")
        return True

    # Mode local par défaut
    upload_data_in_bucket(
        bucket, csv_buffer.getvalue().encode("utf-8-sig"), "air_quality_daily"
    )
    log.info("Données déposées dans le bucket GCP (local mode).")
    return True


def _same_day_previous_month(current_day: date) -> date:
    """Retourne la même date le mois précédent en bornant le jour si nécessaire."""
    if current_day.month == 1:
        target_year = current_day.year - 1
        target_month = 12
    else:
        target_year = current_day.year
        target_month = current_day.month - 1

    max_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(current_day.day, max_day)
    return current_day.replace(year=target_year, month=target_month, day=target_day)


def _upload_city_features(city_name: str, features: list[dict], bucket) -> bool:
    """Upload un CSV par ville en utilisant un nom d'objet dédié."""
    if not features:
        log.info(f"Aucune donnée à sauvegarder pour {city_name}.")
        return False

    csv_buffer = io.StringIO()
    headers = list(features[0]["properties"].keys())

    writer = csv.DictWriter(csv_buffer, fieldnames=headers)
    writer.writeheader()
    for feat in features:
        writer.writerow(feat["properties"])

    upload_data_in_bucket(
        bucket,
        csv_buffer.getvalue().encode("utf-8-sig"),
        f"air_quality_{city_name}",
    )
    log.info(f"Données déposées dans le bucket GCP pour {city_name}.")
    return True


def _get_bucket_or_log_error():
    bucket = connect_to_bucket()
    if bucket is None:
        log.error("Impossible de se connecter au bucket GCP pour l'upload.")
    return bucket


def get_jwt_token():
    username = os.getenv("ATMO_USERNAME")
    password = os.getenv("ATMO_PASSWORD")
    url = "https://admindata.atmo-france.org/api/login"
    payload = {"username": username, "password": password}
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            token = response.json().get("token")
            if token:
                log.info("Token JWT récupéré automatiquement.")
                return token
            else:
                log.error("Erreur : le token n'a pas été trouvé dans la réponse.")
        else:
            log.error(
                f"Erreur lors de la connexion à l'API ATMO : {response.status_code} {response.text}"
            )
    except Exception as e:
        log.error(f"Erreur lors de la récupération automatique du token JWT : {e}")
    return None


def get_atmo_index(
    code_insee="",
    date_histo="",
    aasqa="",
    date_jour: str | None = None,
    jwt_token=None,
):
    """
    Récupère l'indice ATMO pour une commune donnée (code INSEE) à la date spécifiée, format geojson.
    """
    if jwt_token is None:
        jwt_token = get_jwt_token()
    if not jwt_token:
        return None

    date_str = date_jour or date.today().isoformat()
    log.info(
        f"Plage de récupération des données ATMO : date={date_str}, date_historique={date_histo}, code_insee={code_insee}, aasqa={aasqa}"
    )
    params = {
        "format": "geojson",
        "date": date_str,
        "date_historique": date_histo,
        "code_insee": code_insee,
        "aasqa": aasqa,
    }
    headers = {"accept": "*/*", "Authorization": f"Bearer {jwt_token}"}
    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
    except requests.RequestException as e:
        log.error(f"Erreur API ATMO : {e}")
        return None

    if response.status_code != 200:
        log.error(f"Erreur API : {response.status_code} {response.text}")
        return None
    return response.json()


def init_ingestion() -> None:
    """Récupère les données ATMO sur le mois précédent et dépose un CSV par ville."""
    jwt_token = get_jwt_token()
    if not jwt_token:
        log.error("Impossible d'initialiser l'ingestion sans token JWT.")
        return

    today = date.today()
    current_day = today.isoformat()
    historical_day = _same_day_previous_month(today).isoformat()
    # historical_day = "2026-04-01"  # Date fixe pour les tests
    bucket = None

    for city_name, city_config in CITIES.items():
        data = get_atmo_index(
            code_insee=city_config["insee_commune"],
            date_histo=historical_day,
            aasqa=str(city_config["code_aasqa"]),
            date_jour=current_day,
            jwt_token=jwt_token,
        )

        if not data or "features" not in data:
            log.info(f"Aucune donnée reçue de l'API pour {city_name}.")
            continue

        if bucket is None:
            bucket = _get_bucket_or_log_error()
            if bucket is None:
                return

        _upload_city_features(city_name, data["features"], bucket)


def run_ingestion(date_jour: str | None = None) -> None:
    """Récupère les données ATMO du jour et dépose un seul CSV dans le bucket."""
    jwt_token = get_jwt_token()
    if not jwt_token:
        log.error("Impossible d'exécuter l'ingestion sans token JWT.")
        return

    data = get_atmo_index(
        code_insee="",
        date_histo="",
        aasqa="",
        date_jour=date_jour or date.today().isoformat(),
        jwt_token=jwt_token,
    )

    if not data or "features" not in data:
        log.info("Aucune donnée reçue de l'API.")
        return

    # Callback Airflow ?
    upload_callback = globals().get("_air_quality_upload_callback", None)
    if upload_callback is not None:
        save_air_quality_to_bucket(data["features"], None)
        return

    bucket = _get_bucket_or_log_error()
    if bucket is None:
        return

    save_air_quality_to_bucket(data["features"], bucket)


if __name__ == "__main__":
    # run_ingestion(date.today().isoformat())
    init_ingestion()
