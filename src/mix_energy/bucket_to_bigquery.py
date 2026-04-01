import os
from google.cloud import bigquery, storage
from google.oauth2 import service_account

from mix_energy import get_logger
from mix_energy.bigquery_loader import load_all_from_schemas
from mix_energy.bigquery_schema_generator import generate_all_schemas


# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")
PREFIX = os.getenv("PREFIX")
SCHEMA_SAMPLE_ROWS = int(os.getenv("SCHEMA_SAMPLE_ROWS", "500"))


log = get_logger()


def run_transfer():
    if not PROJECT_ID or not DATASET_ID or not BUCKET_NAME:
        raise ValueError(
            "PROJECT_ID, DATASET_ID et BUCKET_NAME doivent etre definis dans l'environnement"
        )

    json_credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not json_credentials_file:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS doit etre defini")

    credentials = service_account.Credentials.from_service_account_file(
        json_credentials_file
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
    gcs_client = storage.Client(project=PROJECT_ID, credentials=credentials)
    bucket = gcs_client.bucket(BUCKET_NAME)

    # 1. Lister les CSV dans le bucket
    blobs = list(bucket.list_blobs(prefix=PREFIX))
    csv_blobs = [b for b in blobs if b.name.endswith(".csv")]
    log.info(
        f"{len(csv_blobs)} fichier(s) CSV trouvé(s) dans gs://{BUCKET_NAME}/{PREFIX}"
    )

    # 2. Traiter tous les fichiers pour supporter le mode post-initialisation
    if not csv_blobs:
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
    run_transfer()
