import argparse
import os
from typing import Any
from google.cloud import bigquery, storage
from google.oauth2 import service_account

from mix_energy import get_logger
from mix_energy.bigquery_loader import load_all_from_schemas
from mix_energy.bigquery_schema_generator import generate_all_schemas

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID_PROD")
BUCKET_NAME = os.getenv("BUCKET_NAME")
PREFIX = os.getenv("PREFIX")
SCHEMA_SAMPLE_ROWS = int(os.getenv("SCHEMA_SAMPLE_ROWS", "500"))
log = get_logger()


def _filter_csv_blobs_by_filename_prefix(
    csv_blobs: list[Any], file_prefix: str | None
) -> list[Any]:
    if not file_prefix:
        return csv_blobs

    normalized_prefix = file_prefix.lower()
    filtered_blobs = []
    skipped_files = []

    for blob in csv_blobs:
        filename = blob.name.split("/")[-1]
        if filename.lower().startswith(normalized_prefix):
            filtered_blobs.append(blob)
        else:
            skipped_files.append(filename)

    log.info(
        "Filtre par prefixe '{}': {} fichier(s) conserve(s), {} fichier(s) ignore(s).",
        file_prefix,
        len(filtered_blobs),
        len(skipped_files),
    )

    return filtered_blobs


def _build_clients_from_local_credentials():
    json_credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not json_credentials_file:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS doit etre defini")

    credentials = service_account.Credentials.from_service_account_file(
        json_credentials_file
    )
    return (
        bigquery.Client(project=PROJECT_ID, credentials=credentials),
        storage.Client(project=PROJECT_ID, credentials=credentials),
    )


def run_transfer(
    file_prefix: str | None = None,
    bq_client: bigquery.Client | None = None,
    gcs_client: storage.Client | None = None,
):
    if not PROJECT_ID or not DATASET_ID or not BUCKET_NAME:
        raise ValueError(
            "PROJECT_ID, DATASET_ID et BUCKET_NAME doivent etre definis dans l'environnement"
        )

    if bq_client is None or gcs_client is None:
        bq_client, gcs_client = _build_clients_from_local_credentials()

    bucket = gcs_client.bucket(BUCKET_NAME)

    # 1. Lister les CSV dans le bucket
    blobs = list(bucket.list_blobs(prefix=PREFIX))
    csv_blobs = [b for b in blobs if b.name.endswith(".csv")]
    csv_blobs = _filter_csv_blobs_by_filename_prefix(csv_blobs, file_prefix)
    log.info(
        f"{len(csv_blobs)} fichier(s) CSV trouvé(s) dans gs://{BUCKET_NAME}/{PREFIX}"
    )

    # 2. Traiter tous les fichiers en mode overwrite systematique
    if not csv_blobs:
        if file_prefix:
            log.warning(
                "Aucun fichier CSV ne correspond au prefixe '{}'. Fin du pipeline.",
                file_prefix,
            )
        else:
            log.info("Aucun fichier CSV a charger. Fin du pipeline.")
        return

    log.info(f"{len(csv_blobs)} fichier(s) a traiter.")

    blob_names = [b.name for b in csv_blobs]

    # 3. Generer les schemas en dictionnaire, cle par nom de fichier CSV
    schema_dict = generate_all_schemas(
        gcs_client=gcs_client,
        bucket_name=BUCKET_NAME,
        blob_names=blob_names,
        sample_rows=SCHEMA_SAMPLE_ROWS,
    )

    # 4. Charger les fichiers en appliquant le schema correspondant
    load_all_from_schemas(
        bq_client=bq_client,
        bucket_name=BUCKET_NAME,
        blob_names=blob_names,
        schema_dict=schema_dict,
    )

    log.info("Transfert termine.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Charge des fichiers CSV depuis GCS vers BigQuery en filtrant optionnellement "
            "par prefixe de nom de fichier."
        )
    )
    parser.add_argument(
        "file_prefix",
        nargs="?",
        default=None,
        help=(
            "Prefixe du nom de fichier a charger, par exemple 'eco2mix-national-cons' "
            "ou 'air_quality'."
        ),
    )
    args = parser.parse_args()

    run_transfer(file_prefix=args.file_prefix)
