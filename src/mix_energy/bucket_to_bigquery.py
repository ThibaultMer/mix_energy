import time
import logging
import pandas as pd
import os
from io import BytesIO
from datetime import datetime
from google.cloud import bigquery, storage
from google.oauth2 import service_account


# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")
PREFIX = os.getenv("PREFIX")


# ─────────────────────────────────────────
# Logging
# ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def get_table_id(filename: str) -> str:
    """
    Dérive le nom de table BigQuery depuis le nom de fichier.
    Ex : 'ventes_2024.csv' → 'ton-projet.ton_dataset.ventes_2024'
    """
    table_name = filename.replace(".csv", "").replace("-", "_").replace(" ", "_")
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"


def create_bigquery_schema(df: pd.DataFrame) -> list[bigquery.SchemaField]:
    """
    Crée un schéma compatible BigQuery à partir d'un DataFrame pandas.
    Gère correctement les valeurs vides et ambigtes.

    Args:
        df: DataFrame pour lequel le schéma doit être créé

    Returns:
        Liste de champs BigQuery (SchemaField)
    """
    schema = []
    for column_name, dtype in df.dtypes.items():
        col_str = str(column_name).lower()

        # Règles de nommage spécifiques
        if "time" in col_str or "timestamp" in col_str:
            bigquery_type = "TIMESTAMP"
        elif "date" in col_str and "heure" not in col_str:
            bigquery_type = "DATE"
        elif "heure" in col_str or "datetime" in col_str:
            bigquery_type = "DATETIME"
        elif pd.api.types.is_bool_dtype(dtype):
            bigquery_type = "BOOLEAN"
        elif pd.api.types.is_integer_dtype(dtype):
            bigquery_type = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            bigquery_type = "FLOAT"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            bigquery_type = "TIMESTAMP"
        elif pd.api.types.is_string_dtype(dtype) or dtype == "object":
            bigquery_type = "STRING"
        else:
            bigquery_type = "STRING"

        # Compter les non-nulls pour debug
        non_null_count = df[column_name].notna().sum()
        total_count = len(df)
        log.info(
            f"    {column_name}: {bigquery_type} ({non_null_count}/{total_count} non-vides)"
        )

        schema.append(
            bigquery.SchemaField(
                name=str(column_name), field_type=bigquery_type, mode="NULLABLE"
            )
        )
    return schema


def create_all_string_schema(df: pd.DataFrame) -> list[bigquery.SchemaField]:
    """Crée un schéma BigQuery avec toutes les colonnes en STRING NULLABLE."""
    schema = [
        bigquery.SchemaField(
            name=str(column_name), field_type="STRING", mode="NULLABLE"
        )
        for column_name in df.columns
    ]
    log.info(f"Schéma de secours STRING généré avec {len(schema)} colonnes")
    return schema


def get_loaded_files(client: bigquery.Client) -> set[str]:
    """
    Récupère la liste des fichiers déjà chargés depuis la table de suivi.
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}._loaded_files"
    try:
        rows = client.query(f"SELECT filename FROM `{table_id}`").result()
        return {row.filename for row in rows}
    except Exception:
        # La table n'existe pas encore → aucun fichier chargé
        return set()


def mark_file_as_loaded(client: bigquery.Client, filename: str):
    """
    Enregistre le fichier dans la table de suivi après un chargement réussi.
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}._loaded_files"
    rows = [
        {
            "filename": filename,
            "loaded_at": datetime.utcnow().isoformat(),
        }
    ]

    # Crée la table de suivi si elle n'existe pas
    schema = [
        bigquery.SchemaField("filename", "STRING"),
        bigquery.SchemaField("loaded_at", "TIMESTAMP"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table, exists_ok=True)

    errors = client.insert_rows_json(table_id, rows)
    if errors:
        log.warning(f"Impossible d'enregistrer {filename} dans le suivi : {errors}")


def load_csv_to_bigquery(
    bq_client: bigquery.Client,
    uri: str,
    table_id: str,
    schema: list[bigquery.SchemaField] | None = None,
) -> bool:
    """
    Charge un fichier CSV depuis GCS vers BigQuery en mode APPEND.
    Retourne True si le chargement a réussi.
    """
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        autodetect=schema is None,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,  # ajout des nouvelles lignes
        field_delimiter=";",
        # Optionnel : ignore les lignes mal formées (à désactiver si tu veux être strict)
        # max_bad_records=10,
    )

    log.info(f"Chargement de {uri} → {table_id} ...")
    load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)

    # Attente avec monitoring
    while not load_job.done():
        log.info(f"  Statut : {load_job.state} ...")
        time.sleep(5)
        load_job.reload()

    if load_job.errors:
        log.error(f"❌ Erreurs pour {uri} : {load_job.errors}")
        return False

    table = bq_client.get_table(table_id)
    log.info(f"✅ Succès — {table.num_rows} lignes total dans {table_id}")
    return True


# ─────────────────────────────────────────
# Pipeline principal
# ─────────────────────────────────────────
def read_csv_from_gcs(gcs_client: storage.Client, uri: str) -> pd.DataFrame:
    """
    Lit un fichier CSV depuis GCS pour inférer le schéma.
    - Lit le fichier COMPLET
    - Gère les valeurs vides correctement
    """
    bucket_name = uri.split("/")[2]
    blob_path = uri.replace(f"gs://{bucket_name}/", "")

    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    csv_data = blob.download_as_bytes()
    # Lire tout le fichier, pas limité à nrows
    df = pd.read_csv(
        BytesIO(csv_data),
        sep=";",
        dtype=str,  # Lire tout en string d'abord
        keep_default_na=True,
        na_values=["", "NA", "N/A", "null", "NULL", "-"],
    )

    # Convertir intelligemment les colonnes
    for col in df.columns:
        col_lower = str(col).lower()

        # Essayer conversions intelligentes
        if "date" in col_lower or "time" in col_lower:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except ValueError:
                print("Entrée invalide")
        else:
            # Essayer int, puis float, sinon garder string
            try:
                if df[col].notna().sum() > 0:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            except ValueError:
                print("Entrée invalide")

    return df


def run_transfer():
    json_credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials = service_account.Credentials.from_service_account_file(
        json_credentials_file
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
    gcs_client = storage.Client(project=PROJECT_ID, credentials=credentials)
    bucket = gcs_client.bucket(BUCKET_NAME)

    # 1. Fichiers déjà traités
    loaded_files = get_loaded_files(bq_client)
    log.info(f"{len(loaded_files)} fichier(s) déjà chargé(s) en base.")

    # 2. Lister les CSV dans le bucket
    blobs = list(bucket.list_blobs(prefix=PREFIX))
    csv_blobs = [b for b in blobs if b.name.endswith(".csv")]
    log.info(
        f"{len(csv_blobs)} fichier(s) CSV trouvé(s) dans gs://{BUCKET_NAME}/{PREFIX}"
    )

    # 3. Ne traiter que les nouveaux fichiers
    new_blobs = [b for b in csv_blobs if b.name not in loaded_files]
    if not new_blobs:
        log.info("Aucun nouveau fichier à charger. Fin du pipeline.")
        return

    log.info(f"{len(new_blobs)} nouveau(x) fichier(s) à charger.")

    # 4. Charger chaque fichier avec son propre schéma inféré
    for blob in new_blobs:
        uri = f"gs://{BUCKET_NAME}/{blob.name}"
        filename = blob.name.split("/")[-1]  # ex : "ventes_2024.csv"
        table_id = get_table_id(filename)

        inferred_schema = None
        df_sample = None
        try:
            log.info(f"Inférence du schéma depuis {filename}...")
            df_sample = read_csv_from_gcs(gcs_client, uri)
            log.info(
                f"  Fichier lu : {len(df_sample)} lignes, {len(df_sample.columns)} colonnes"
            )
            inferred_schema = create_bigquery_schema(df_sample)
            log.info(f"✓ Schéma BigQuery généré avec {len(inferred_schema)} colonnes")
        except Exception as e:
            log.warning(
                f"Impossible d'inférer le schéma pour {filename} : {e}. Utilisation de autodetect."
            )

        success = load_csv_to_bigquery(bq_client, uri, table_id, schema=inferred_schema)

        if not success and df_sample is not None:
            log.warning(
                f"Nouvelle tentative pour {filename} avec schéma de secours STRING..."
            )
            fallback_schema = create_all_string_schema(df_sample)
            success = load_csv_to_bigquery(
                bq_client, uri, table_id, schema=fallback_schema
            )

        if success:
            mark_file_as_loaded(bq_client, blob.name)


if __name__ == "__main__":
    run_transfer()
