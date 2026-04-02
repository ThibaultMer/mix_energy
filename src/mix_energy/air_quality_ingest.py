import requests
import csv
import os

from datetime import date


# URL de l'API ATMO France (API Qualité de l'air)
BASE_URL = "https://admindata.atmo-france.org/api/v2/data/indices/atmo"


def get_jwt_token():
    username = os.getenv("ATMO_USERNAME")
    password = os.getenv("ATMO_PASSWORD")
    url = "https://admindata.atmo-france.org/api/login"
    payload = {"username": username, "password": password}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            token = response.json().get("token")
            print("Token JWT récupéré :", token)
            if token:
                print("Token JWT récupéré automatiquement.")
                return token
            else:
                print("Erreur : le token n'a pas été trouvé dans la réponse.")
        else:
            print(
                f"Erreur lors de la connexion à l'API ATMO : {response.status_code} {response.text}"
            )
    except Exception as e:
        print(f"Erreur lors de la récupération automatique du token JWT : {e}")
    return None


def get_atmo_index(code_insee="", date_histo="", aasqa="", jwt_token=None):
    """
    Récupère l'indice ATMO pour une commune donnée (code INSEE) à la date spécifiée, format geojson.
    """
    if jwt_token is None:
        jwt_token = get_jwt_token()
    if not jwt_token:
        return None
    # Utilise la date du jour au format YYYY-MM-DD si aucune date_histo n'est fournie
    date_str = date.today().isoformat()
    print(date_str)
    print(date_histo)
    params = {
        "format": "geojson",
        "date": date_str,
        "date_historique": date_histo,
        "code_insee": code_insee,
        "aasqa": aasqa,
    }
    headers = {"accept": "*/*", "Authorization": f"Bearer {jwt_token}"}
    response = requests.get(BASE_URL, params=params, headers=headers)
    if response.status_code != 200:
        print("Erreur API :", response.status_code, response.text)
        return None
    return response.json()


if __name__ == "__main__":
    data = get_atmo_index(code_insee="", date_histo="2026-03-01", aasqa="44")

    if data and "features" in data:
        # Préparer le chemin du fichier CSV
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
        )
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "air_quality_national.csv")

        # Extraire les propriétés des features
        features = data["features"]
        if features:
            # Utiliser les clés du premier élément comme en-têtes CSV
            headers = list(features[0]["properties"].keys())
            with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                for feat in features:
                    writer.writerow(feat["properties"])
            print(f"Données sauvegardées dans {output_file}")
        else:
            print("Aucune donnée à sauvegarder.")
    else:
        print("Aucune donnée reçue de l'API.")
