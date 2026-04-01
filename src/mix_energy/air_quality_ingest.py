

import requests
import csv
import os

# URL de l'API ATMO France (API Qualité de l'air)
BASE_URL = "https://admindata.atmo-france.org/api/v2/data/indices/atmo"
JWT_TOKEN = os.getenv("JWT_TOKEN")


def get_jwt_token():
    token = os.getenv("JWT_TOKEN")
    if token:
        return token
    # Sinon, tente de récupérer automatiquement le token via /api/login
    username = os.getenv("ATMO_USERNAME") or "asticot"
    password = os.getenv("ATMO_PASSWORD") or "p7g^2>B#vB-)jw9"
    url = "https://admindata.atmo-france.org/api/login"
    payload = {"username": username, "password": password}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            token = response.json().get("token")
            if token:
                print("Token JWT récupéré automatiquement.")
                return token
            else:
                print("Erreur : le token n'a pas été trouvé dans la réponse.")
        else:
            print(f"Erreur lors de la connexion à l'API ATMO : {response.status_code} {response.text}")
    except Exception as e:
        print(f"Erreur lors de la récupération automatique du token JWT : {e}")
    return None

def get_atmo_index_geojson(date="2026-03-31", code_insee="", jwt_token=None):
    """
    Récupère l'indice ATMO pour une commune donnée (code INSEE) à la date spécifiée, format geojson.
    """
    if jwt_token is None:
        jwt_token = get_jwt_token()
    if not jwt_token:
        return None
    params = {
        "format": "geojson",
        "date": date,
        "code_insee": code_insee
    }
    headers = {
        "accept": "*/*",
        "Authorization": f"Bearer {jwt_token}"
    }
    response = requests.get(BASE_URL, params=params, headers=headers)
    if response.status_code != 200:
        print("Erreur API :", response.status_code, response.text)
        return None
    return response.json()

# Exemple d'utilisation : récupérer l'indice ATMO national à la date du 8 juin 2024

if __name__ == "__main__":
    code_insee = ""
    data = get_atmo_index_geojson(code_insee=code_insee)
    if data and "features" in data:
        # Préparer le chemin du fichier CSV
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
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




#get_atmo_index(insee="75056")  # Paris

#get_atmo_index(city="Marseille", date="2026-03-31")
#get_atmo_index(insee="13055", date="2026-03-31")  # Marseille





