from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from airflow.sdk import dag, task
from airflow.providers.google.cloud.hooks.gcs import GCSHook

from mix_energy.base_carbone_ingest import get_base_carbone
from mix_energy.bucket_to_bigquery_airflow import run_transfer as _run_transfer

DATASET_ID = "base_carbone"
FILE_PREFIX = "base_carbone"
GCP_CONN_ID = "google_cloud_default"
BUCKET_NAME = os.getenv("BUCKET_NAME", "mix-energie-bucket")


@dag(
    dag_id="dag_base_carbone",
    description="Ingestion base carbone vers GCS.",
    start_date=datetime(2026, 1, 1),
    schedule="30 9 1 * 1-5",
    catchup=False,
    tags=["base_carbone", "ingestion"],
)
def dag_base_carbone():
    @task(task_id="check_bucket_connection")
    def check_bucket_connection() -> str:
        hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        try:
            # Use object listing to validate access without requiring storage.buckets.get.
            hook.list(bucket_name=BUCKET_NAME, max_results=1)
        except Exception as exc:
            raise RuntimeError("Connexion au bucket GCP impossible.") from exc
        return BUCKET_NAME

    @task(task_id="ingest_csv_to_bucket")
    def ingest_csv_to_bucket(bucket_name: str) -> None:
        df = get_base_carbone()
        if df is None or df.empty:
            raise RuntimeError("Recuperation base carbone echouee.")

        csv_content = df.to_csv(index=False, sep=";").encode("utf-8")
        if len(csv_content) == 0:
            raise RuntimeError("CSV vide recupere pour base_carbone.")

        if BUCKET_NAME != bucket_name:
            raise RuntimeError(
                f"Bucket inattendu: '{BUCKET_NAME}' (attendu: '{bucket_name}')."
            )

        hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        hook.upload(
            bucket_name=bucket_name,
            object_name=f"{DATASET_ID}.csv",
            data=csv_content,
        )

    @task(task_id="transfer_csv_to_bigquery")
    def transfer_csv_from_bucket_to_bigquery() -> None:
        _run_transfer(file_prefix=FILE_PREFIX, gcp_conn_id=GCP_CONN_ID)

    check_bucket_connection_task: Any = check_bucket_connection()
    ingest_csv_to_bucket_task: Any = ingest_csv_to_bucket(
        bucket_name=check_bucket_connection_task,
    )
    transfer_csv_from_bucket_to_bigquery_task: Any = (
        transfer_csv_from_bucket_to_bigquery()
    )

    (
        check_bucket_connection_task
        >> ingest_csv_to_bucket_task
        >> transfer_csv_from_bucket_to_bigquery_task
    )


dag = dag_base_carbone()
