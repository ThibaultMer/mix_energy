import requests
import csv
import os

# URL de l'API ATMO France (API Qualité de l'air)
BASE_URL = "https://admindata.atmo-france.org/api/v2/data/indices/atmo"

jwt_token = os.getenv("JWT_TOKEN")


def get_atmo_index_geojson(date="2024-06-08", code_insee="75056"):
    """
    Récupère l'indice ATMO pour une commune donnée (code INSEE) à la date spécifiée, format geojson.
    """
    params = {"format": "geojson", "date": date, "code_insee": code_insee}
    headers = {"accept": "*/*", "Authorization": f"Bearer {jwt_token}"}
    response = requests.get(BASE_URL, params=params, headers=headers)
    if response.status_code != 200:
        print("Erreur API :", response.status_code, response.text)
        return None
    return response.json()


# Exemple d'utilisation : récupérer l'indice ATMO de Paris à la date du 8 juin 2024

if __name__ == "__main__":
    code_insee = "50640"
    data = get_atmo_index_geojson(code_insee=code_insee)
    if data and "features" in data:
        # Préparer le chemin du fichier CSV
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
        )
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "air_quality.csv")

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


# get_atmo_index(insee="75056")  # Paris

# get_atmo_index(city="Marseille", date="2026-03-31")
# get_atmo_index(insee="13055", date="2026-03-31")  # Marseille
