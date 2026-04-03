import csv
import os
import io
import pandas as pd
import requests

from mix_energy import get_logger
from mix_energy.gcp_utils import connect_to_bucket, upload_data_in_bucket


log = get_logger()


BASE_CARBONE_COLUMNS = [
    ("Type Ligne", "Type de ligne"),
    ("Identifiant de l'élément", "Identifiant"),
    ("Type de l'élément", "Type de l'élément"),
    ("Statut de l'élément", "Statut de l'élément"),
    ("Nom attribut français", "Nom attribut français"),
    ("Unité français", "Unité français"),
    ("Date de création", "Date de création"),
    ("Date de modification", "Date de modification"),
    ("Total poste non décomposé", "Total poste non décomposé"),
]


def _clean_base_carbone_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtre et renomme les colonnes de la base carbone avant upload.
    Garde uniquement les 10 colonnes nécessaires et les renomme selon la politique définie.
    Applique également des filtres de valeurs.
    """
    selected_columns = []
    rename_map = {}

    for source_name, target_name in BASE_CARBONE_COLUMNS:
        if source_name in df.columns:
            selected_columns.append(source_name)
            if source_name != target_name:
                rename_map[source_name] = target_name

    cleaned_df = df.loc[:, selected_columns].copy()

    # Applique les filtres de valeurs
    allowed_types = [
        "centrale charbon",
        "centrale fioul",
        "centrale gaz",
        "centrale nucléaire",
        "éolien en mer",
        "éolien terrestre",
        "photovoltaïque",
    ]
    cleaned_df = cleaned_df[cleaned_df["Nom attribut français"].isin(allowed_types)]
    # Trois lignes sont présentes pour le photovoltaïque.
    # On garde uniquement celle avec l'identifiant 34720
    # Correspond à la ligne par défaut pour les panneaux photovoltaïques. (fabrication Chine)
    photovoltaic_mask = cleaned_df["Nom attribut français"] == "photovoltaïque"
    cleaned_df = cleaned_df[
        ~photovoltaic_mask | (cleaned_df["Identifiant de l'élément"] == "34720")
    ]
    cleaned_df = cleaned_df[cleaned_df["Statut de l'élément"] != "Archivé"]
    cleaned_df = cleaned_df[cleaned_df["Type Ligne"] == "Elément"]

    return cleaned_df.rename(columns=rename_map)


def get_base_carbone():
    """
    Récupère la base carbone de l'Ademe depuis l'URL définie dans les variables d'environnement.
    Renvoie un DataFrame pandas contenant le CSV.
    """

    url = os.getenv("BASE_CARBONE_URL")
    df = pd.DataFrame()
    if not url:
        log.error("BASE_CARBONE_URL n'est pas définie")

    else:
        response = requests.get(url)
        response.raise_for_status()
        log.info(f"URL: {response.url[:50]}...")
        df = pd.read_csv(
            io.BytesIO(response.content), sep=";", encoding="cp1252", dtype=str
        )

        df = _clean_base_carbone_dataframe(df)

        colonne_float = "Total poste non décomposé"
        if colonne_float in df.columns:
            df[colonne_float] = pd.to_numeric(
                df[colonne_float].str.replace(",", ".", regex=False),
                errors="coerce",
            )
        else:
            log.warning(f"La colonne {colonne_float!r} est absente du CSV.")

    return df


def save_base_carbone_to_gcp(df: pd.DataFrame):
    """
    Enregistre le DataFrame de la base carbone dans un bucket GCP.

    Args:
        df: DataFrame contenant les données de la base carbone
    """

    bucket = connect_to_bucket()
    if bucket is not None:
        csv_buffer = io.BytesIO()
        df.to_csv(
            csv_buffer,
            index=False,
            encoding="cp1252",
            sep=";",
            quoting=csv.QUOTE_ALL,
            doublequote=True,
        )
        upload_data_in_bucket(bucket, csv_buffer.getvalue(), "base_carbone")
        log.info("Base carbone enregistrée dans le bucket GCP.")
    else:
        log.error("Impossible de se connecter au bucket GCP pour l'upload.")


def run_ingestion() -> None:
    """Récupère la base carbone et l'enregistre dans le bucket GCP."""
    df = get_base_carbone()
    if not df.empty:
        save_base_carbone_to_gcp(df)
    else:
        log.error(
            "Le DataFrame de la base carbone est vide. Aucune donnée à enregistrer."
        )


if __name__ == "__main__":
    run_ingestion()
