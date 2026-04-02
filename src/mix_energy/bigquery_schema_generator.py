from typing import Any, cast

import pandas as pd
from google.cloud import bigquery, storage

from mix_energy import get_logger


CSV_DELIMITER_SEMICOLON = ";"
CSV_DELIMITER_COMMA = ","
NULL_MARKERS = ["", "NA", "N/A", "null", "NULL", "-", "ND"]

log = get_logger()


def read_csv_from_gcs(
    gcs_client: storage.Client,
    bucket_name: str,
    blob_name: str,
    sample_rows: int,
    delimiter: str,
) -> pd.DataFrame:
    """
    Lit un echantillon d'un CSV depuis GCS pour inferer le schema.
    """
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    with blob.open("rt", encoding="utf-8") as csv_stream:
        df = pd.read_csv(
            cast(Any, csv_stream),
            sep=delimiter,
            dtype=str,
            keep_default_na=True,
            na_values=NULL_MARKERS,
            nrows=sample_rows,
        )

    for col in df.columns:
        col_lower = str(col).lower()
        if "date" in col_lower or "time" in col_lower:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        else:
            if df[col].notna().sum() > 0:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _resolve_generic_type(column_name: Any, dtype: Any) -> str:
    col_str = str(column_name).lower()

    if "time" in col_str or "timestamp" in col_str or "date_heure" in col_str:
        return "TIMESTAMP"
    if "date" in col_str and "heure" not in col_str:
        return "DATE"
    if "heure" in col_str:
        return "STRING"
    if "libelle_region" in col_str or "nature" in col_str or "perimetre" in col_str:
        return "STRING"
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    if pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    if pd.api.types.is_string_dtype(dtype) or dtype == "object":
        return "STRING"
    return "STRING"


def _resolve_eco2mix_type(column_name: Any, dtype: Any) -> str:
    col_str = str(column_name).lower()

    if "time" in col_str or "timestamp" in col_str or "date_heure" in col_str:
        return "TIMESTAMP"
    if "date" in col_str and "heure" not in col_str:
        return "DATE"
    if "heure" in col_str:
        return "STRING"
    if "libelle_region" in col_str or "nature" in col_str or "perimetre" in col_str:
        return "STRING"
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    if pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    if pd.api.types.is_string_dtype(dtype) or dtype == "object":
        return "STRING"

    return "STRING"


def _resolve_meteo_type(column_name: Any, dtype: Any) -> str:
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    if pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    if pd.api.types.is_string_dtype(dtype) or dtype == "object":
        return "STRING"
    return "STRING"


def _resolve_air_quality_type(column_name: Any, dtype: Any) -> str:
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    if pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    if pd.api.types.is_string_dtype(dtype) or dtype == "object":
        return "STRING"
    return "STRING"


def create_generic_schema(df: pd.DataFrame) -> list[bigquery.SchemaField]:
    """Boucle de schema generique pour tous les fichiers non specialises."""
    schema: list[bigquery.SchemaField] = []
    for column_name, dtype in df.dtypes.items():
        bigquery_type = _resolve_generic_type(column_name, dtype)

        non_null_count = df[column_name].notna().sum()
        total_count = len(df)
        log.debug(
            "    [generic] {}: {} ({}/{} non-vides)",
            column_name,
            bigquery_type,
            non_null_count,
            total_count,
        )

        schema.append(
            bigquery.SchemaField(
                name=str(column_name),
                field_type=bigquery_type,
                mode="NULLABLE",
            )
        )
    return schema


def create_eco2mix_schema(df: pd.DataFrame) -> list[bigquery.SchemaField]:
    """Boucle de schema dediee aux fichiers commençant par eco2mix."""
    schema: list[bigquery.SchemaField] = []
    for column_name, dtype in df.dtypes.items():
        bigquery_type = _resolve_eco2mix_type(column_name, dtype)

        non_null_count = df[column_name].notna().sum()
        total_count = len(df)
        log.debug(
            "    [eco2mix] {}: {} ({}/{} non-vides)",
            column_name,
            bigquery_type,
            non_null_count,
            total_count,
        )

        schema.append(
            bigquery.SchemaField(
                name=str(column_name),
                field_type=bigquery_type,
                mode="NULLABLE",
            )
        )
    return schema


def create_meteo_schema(df: pd.DataFrame) -> list[bigquery.SchemaField]:
    """Boucle de schema dediee aux fichiers commençant par meteo."""
    schema: list[bigquery.SchemaField] = []
    for column_name, dtype in df.dtypes.items():
        bigquery_type = _resolve_meteo_type(column_name, dtype)

        non_null_count = df[column_name].notna().sum()
        total_count = len(df)
        log.debug(
            "    [meteo] {}: {} ({}/{} non-vides)",
            column_name,
            bigquery_type,
            non_null_count,
            total_count,
        )

        schema.append(
            bigquery.SchemaField(
                name=str(column_name),
                field_type=bigquery_type,
                mode="NULLABLE",
            )
        )
    return schema


def create_air_quality_schema(df: pd.DataFrame) -> list[bigquery.SchemaField]:
    """Boucle de schema dediee aux fichiers commençant par air_quality."""
    schema: list[bigquery.SchemaField] = []
    for column_name, dtype in df.dtypes.items():
        bigquery_type = _resolve_air_quality_type(column_name, dtype)

        non_null_count = df[column_name].notna().sum()
        total_count = len(df)
        log.debug(
            "    [air_quality] {}: {} ({}/{} non-vides)",
            column_name,
            bigquery_type,
            non_null_count,
            total_count,
        )

        schema.append(
            bigquery.SchemaField(
                name=str(column_name),
                field_type=bigquery_type,
                mode="NULLABLE",
            )
        )
    return schema


def create_bigquery_schema_for_file(
    filename: str, df: pd.DataFrame
) -> list[bigquery.SchemaField]:
    """
    Selectionne la boucle de schema selon le prefixe du nom de fichier CSV.
    """
    filename_lower = filename.lower()

    if filename_lower.startswith("eco2mix"):
        return create_eco2mix_schema(df)
    if filename_lower.startswith("meteo"):
        return create_meteo_schema(df)
    if filename_lower.startswith("air_quality"):
        return create_air_quality_schema(df)
    return create_generic_schema(df)


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


def create_all_string_schema(df: pd.DataFrame) -> list[bigquery.SchemaField]:
    """Cree un schema BigQuery avec toutes les colonnes en STRING NULLABLE."""
    schema = [
        bigquery.SchemaField(
            name=str(column_name),
            field_type="STRING",
            mode="NULLABLE",
        )
        for column_name in df.columns
    ]
    log.info("Schema de secours STRING genere avec %s colonnes", len(schema))
    return schema


def generate_all_schemas(
    gcs_client: storage.Client,
    bucket_name: str,
    blob_names: list[str],
    sample_rows: int,
) -> dict[str, list[bigquery.SchemaField] | None]:
    """
    Genere un dictionnaire de schemas BigQuery cle par nom de fichier CSV.
    """
    schema_dict: dict[str, list[bigquery.SchemaField] | None] = {}

    for blob_name in blob_names:
        filename = blob_name.split("/")[-1]
        if filename in schema_dict:
            log.warning(
                "Collision de nom de fichier detectee pour {}. Le dernier schema remplace l'ancien.",
                filename,
            )

        try:
            delimiter = get_csv_delimiter_for_filename(filename)
            df_sample = read_csv_from_gcs(
                gcs_client,
                bucket_name,
                blob_name,
                sample_rows,
                delimiter,
            )
            schema_dict[filename] = create_bigquery_schema_for_file(filename, df_sample)
            log.info("Schema genere pour {}", filename)
        except Exception as err:
            log.warning(
                "Impossible d'inferer le schema pour {}: {}. Le chargement utilisera autodetect.",
                filename,
                err,
            )
            schema_dict[filename] = None

    return schema_dict
