from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.sdk import dag, task
from airflow.timetables.trigger import MultipleCronTriggerTimetable

from mix_energy import air_quality_ingest as _air_quality_ingest
from mix_energy.bucket_to_bigquery_airflow import run_transfer as _run_transfer

FILE_PREFIX = "air_quality_daily"
GCP_CONN_ID = "google_cloud_default"
BUCKET_NAME = os.getenv("BUCKET_NAME", "mix-energie-bucket")


@dag(
    dag_id="dag_air_quality",
    description="Ingestion air quality vers GCS puis BigQuery.",
    start_date=datetime(2026, 1, 1),
    schedule=MultipleCronTriggerTimetable(
        "30 9 * * 1-5",
        timezone="Europe/Paris",
    ),
    catchup=False,
    tags=["air_quality", "ingestion"],
)
def dag_air_quality():
    @task(task_id="check_bucket_connection")
    def check_bucket_connection() -> str:
        hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        try:
            # Use object listing to validate access without requiring storage.buckets.get.
            hook.list(bucket_name=BUCKET_NAME, max_results=1)
        except Exception as exc:
            raise RuntimeError("Connexion au bucket GCP impossible.") from exc
        return BUCKET_NAME

    @task(task_id="ingest_air_quality_to_bucket")
    def ingest_air_quality_to_bucket(bucket_name: str) -> None:
        atmo_username = os.getenv("ATMO_USERNAME")
        atmo_password = os.getenv("ATMO_PASSWORD")

        if atmo_username is None or atmo_password is None:
            raise RuntimeError(
                "Variables d'environnement ATMO_USERNAME et ATMO_PASSWORD requises."
            )

        if BUCKET_NAME != bucket_name:
            raise RuntimeError(
                f"Bucket inattendu: '{BUCKET_NAME}' (attendu: '{bucket_name}')."
            )

        # Injecte un callback Airflow pour upload GCS
        def airflow_upload_callback(csv_content, object_name):
            hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
            hook.upload(
                bucket_name=bucket_name,
                object_name=f"{object_name}.csv",
                data=csv_content.encode("utf-8")
                if isinstance(csv_content, str)
                else csv_content,
            )

        _air_quality_ingest._air_quality_upload_callback = airflow_upload_callback
        try:
            _air_quality_ingest.run_ingestion()
        finally:
            if hasattr(_air_quality_ingest, "_air_quality_upload_callback"):
                delattr(_air_quality_ingest, "_air_quality_upload_callback")

        hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        uploaded = hook.list(bucket_name=bucket_name, prefix=FILE_PREFIX, max_results=1)
        if not uploaded:
            raise RuntimeError(
                "Aucun fichier air quality n'a ete detecte dans le bucket apres ingestion."
            )

    @task(task_id="transfer_csv_to_bigquery")
    def transfer_csv_from_bucket_to_bigquery(file_prefix: str) -> None:
        _run_transfer(file_prefix=file_prefix, gcp_conn_id=GCP_CONN_ID)

    check_bucket_connection_task: Any = check_bucket_connection()
    ingest_air_quality_to_bucket_task: Any = ingest_air_quality_to_bucket(
        bucket_name=check_bucket_connection_task,
    )
    transfer_csv_from_bucket_to_bigquery_task: Any = (
        transfer_csv_from_bucket_to_bigquery(file_prefix=FILE_PREFIX)
    )

    (
        check_bucket_connection_task
        >> ingest_air_quality_to_bucket_task
        >> transfer_csv_from_bucket_to_bigquery_task
    )


dag = dag_air_quality()
