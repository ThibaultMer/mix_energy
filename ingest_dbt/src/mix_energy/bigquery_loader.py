import os
import time
from datetime import datetime, timezone

from google.cloud import bigquery

from mix_energy import get_logger


PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID_PROD")

CSV_DELIMITER_SEMICOLON = ";"
CSV_DELIMITER_COMMA = ","
NULL_MARKERS = ["", "NA", "N/A", "null", "NULL", "-", "ND"]

log = get_logger()


def _normalize_table_name(filename: str) -> str:
    return filename.replace(".csv", "").replace("-", "_").replace(" ", "_")


def get_csv_delimiter_for_filename(filename: str) -> str:
    """
    Determine le separateur CSV selon le prefixe du fichier.
    - meteo* et air_quality* -> virgule
    - eco2mix* et autres -> point-virgule
    """
    filename_lower = filename.lower()
    if filename_lower.startswith("meteo") or filename_lower.startswith("air_quality"):
        return CSV_DELIMITER_COMMA
    return CSV_DELIMITER_SEMICOLON


def get_table_id(filename: str) -> str:
    """
    Derive le nom de table BigQuery depuis le nom de fichier.
    """
    table_name = _normalize_table_name(filename)
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"


def get_loaded_files(client: bigquery.Client) -> set[str]:
    """
    Recupere la liste des fichiers deja charges depuis la table de suivi.
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}._loaded_files"
    try:
        rows = client.query(f"SELECT filename FROM `{table_id}`").result()
        return {row.filename for row in rows}
    except Exception:
        return set()


def mark_file_as_loaded(client: bigquery.Client, filename: str):
    """
    Enregistre le fichier dans la table de suivi apres un chargement reussi.
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}._loaded_files"
    rows = [
        {
            "filename": filename,
            "loaded_at": datetime.now(timezone.utc).isoformat(),
        }
    ]

    schema = [
        bigquery.SchemaField("filename", "STRING"),
        bigquery.SchemaField("loaded_at", "TIMESTAMP"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table, exists_ok=True)

    errors = client.insert_rows_json(table_id, rows)
    if errors:
        log.warning("Impossible d'enregistrer {} dans le suivi : {}", filename, errors)


def load_csv_to_bigquery(
    bq_client: bigquery.Client,
    uri: str,
    table_id: str,
    schema: list[bigquery.SchemaField] | None = None,
    write_disposition: str = bigquery.WriteDisposition.WRITE_TRUNCATE,
    field_delimiter: str = CSV_DELIMITER_SEMICOLON,
) -> bool:
    """
    Charge un fichier CSV depuis GCS vers BigQuery.
    """
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        autodetect=schema is None,
        write_disposition=write_disposition,
        field_delimiter=field_delimiter,
        null_markers=NULL_MARKERS,
    )

    log.info("Chargement de {} -> {} ...", uri, table_id)
    load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)

    while not load_job.done():
        log.info("  Statut : {} ...", load_job.state)
        time.sleep(5)
        load_job.reload()

    if load_job.errors:
        log.error("Erreurs pour {} : {}", uri, load_job.errors)
        return False

    table = bq_client.get_table(table_id)
    log.info("Succes - {} lignes total dans {}", table.num_rows, table_id)
    return True


def _create_string_schema_from_schema(
    schema: list[bigquery.SchemaField],
) -> list[bigquery.SchemaField]:
    return [
        bigquery.SchemaField(name=field.name, field_type="STRING", mode="NULLABLE")
        for field in schema
    ]


def load_all_from_schemas(
    bq_client: bigquery.Client,
    bucket_name: str,
    blob_names: list[str],
    schema_dict: dict[str, list[bigquery.SchemaField] | None],
):
    """
    Charge chaque CSV dans BigQuery en appliquant le schema correspondant.
    Le chargement ecrase toujours la table cible.
    """
    for blob_name in blob_names:
        filename = blob_name.split("/")[-1]
        uri = f"gs://{bucket_name}/{blob_name}"
        schema = schema_dict.get(filename)
        field_delimiter = get_csv_delimiter_for_filename(filename)

        table_id = get_table_id(filename)
        write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        log.info("LOAD {} -> {} (WRITE_TRUNCATE)", filename, table_id)

        success = load_csv_to_bigquery(
            bq_client,
            uri,
            table_id,
            schema=schema,
            write_disposition=write_disposition,
            field_delimiter=field_delimiter,
        )

        if not success and schema is not None:
            log.warning(
                "Nouvelle tentative pour {} avec schema de secours STRING...", filename
            )
            fallback_schema = _create_string_schema_from_schema(schema)
            success = load_csv_to_bigquery(
                bq_client,
                uri,
                table_id,
                schema=fallback_schema,
                write_disposition=write_disposition,
                field_delimiter=field_delimiter,
            )

        if success:
            mark_file_as_loaded(bq_client, blob_name)
