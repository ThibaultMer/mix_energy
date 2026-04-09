from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from airflow.sdk import dag, task
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.timetables.trigger import MultipleCronTriggerTimetable

from mix_energy import meteo_ingest as _meteo_ingest
from mix_energy.bucket_to_bigquery_airflow import run_transfer as _run_transfer

FILE_PREFIX = "meteo_"
GCP_CONN_ID = "google_cloud_default"
BUCKET_NAME = os.getenv("BUCKET_NAME", "mix-energie-bucket")


@dag(
    dag_id="dag_meteo",
    description="Ingestion meteo vers GCS puis BigQuery.",
    start_date=datetime(2026, 1, 1),
    schedule=MultipleCronTriggerTimetable(
        "30 9 * * 1-5",
        timezone="Europe/Paris",
    ),
    catchup=False,
    tags=["meteo", "ingestion"],
)
def dag_meteo():
    @task(task_id="check_bucket_connection")
    def check_bucket_connection() -> str:
        hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        try:
            # Use object listing to validate access without requiring storage.buckets.get.
            hook.list(bucket_name=BUCKET_NAME, max_results=1)
        except Exception as exc:
            raise RuntimeError("Connexion au bucket GCP impossible.") from exc
        return BUCKET_NAME

    @task(task_id="ingest_meteo_to_bucket")
    def ingest_meteo_to_bucket(bucket_name: str) -> None:
        past_days = os.getenv("PAST_DAYS")
        forecast_days = os.getenv("FORCAST_DAYS")

        if past_days is None or forecast_days is None:
            raise RuntimeError(
                "Variables d'environnement PAST_DAYS et FORCAST_DAYS requises."
            )

        try:
            parsed_past_days = int(past_days)
            parsed_forecast_days = int(forecast_days)
        except ValueError as exc:
            raise RuntimeError(
                "PAST_DAYS et FORCAST_DAYS doivent etre des entiers."
            ) from exc

        if BUCKET_NAME != bucket_name:
            raise RuntimeError(
                f"Bucket inattendu: '{BUCKET_NAME}' (attendu: '{bucket_name}')."
            )

        # Inject Airflow GCS upload callback for dual-mode
        def airflow_upload_callback(csv_content, city_name):
            hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
            object_name = f"meteo_{city_name}.csv"
            hook.upload(
                bucket_name=bucket_name,
                object_name=object_name,
                data=csv_content.encode("utf-8")
                if isinstance(csv_content, str)
                else csv_content,
            )

        _meteo_ingest.past_days = parsed_past_days
        _meteo_ingest.forecast_days = parsed_forecast_days
        # Set the callback globally for the ingestion module
        _meteo_ingest._meteo_upload_callback = airflow_upload_callback
        try:
            _meteo_ingest.run_ingestion()
        finally:
            # Clean up to avoid side effects if run in other contexts
            if hasattr(_meteo_ingest, "_meteo_upload_callback"):
                delattr(_meteo_ingest, "_meteo_upload_callback")

    @task(task_id="transfer_csv_to_bigquery")
    def transfer_csv_from_bucket_to_bigquery(file_prefix: str) -> None:
        _run_transfer(file_prefix=file_prefix, gcp_conn_id=GCP_CONN_ID)

    check_bucket_connection_task: Any = check_bucket_connection()
    ingest_meteo_to_bucket_task: Any = ingest_meteo_to_bucket(
        bucket_name=check_bucket_connection_task,
    )
    transfer_csv_from_bucket_to_bigquery_task: Any = (
        transfer_csv_from_bucket_to_bigquery(file_prefix=FILE_PREFIX)
    )

    (
        check_bucket_connection_task
        >> ingest_meteo_to_bucket_task
        >> transfer_csv_from_bucket_to_bigquery_task
    )


dag = dag_meteo()
