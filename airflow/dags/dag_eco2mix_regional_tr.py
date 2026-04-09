from __future__ import annotations

import os

from datetime import datetime
from typing import Any

from airflow.sdk import dag, task
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.timetables.trigger import MultipleCronTriggerTimetable

from mix_energy.bucket_to_bigquery_airflow import run_transfer as _run_transfer
from mix_energy.eco2mix_ingest import retrieve_csv as _retrieve_csv

from airflow.operators.bash import BashOperator

DATASET_ID = "eco2mix-regional-tr"
FILE_PREFIX = "eco2mix-regional-tr"
GCP_CONN_ID = "google_cloud_default"
BUCKET_NAME = os.getenv("BUCKET_NAME", "mix-energie-bucket")


@dag(
    dag_id="dag_eco2mix_regional_tr",
    description="Ingestion eco2mix regional tr vers GCS.",
    start_date=datetime(2026, 1, 1),
    schedule=MultipleCronTriggerTimetable(
        "30,45 9 * * 1-5",
        "0,15,30,45 10-17 * * 1-5",
        "0,15,30 18 * * 1-5",
        timezone="Europe/Paris",
    ),
    catchup=False,
    tags=["eco2mix", "ingestion"],
)
def dag_eco2mix_regional_tr():
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
    def ingest_csv_to_bucket(bucket_name: str, dataset_id: str) -> None:
        csv_content = _retrieve_csv(dataset_id=dataset_id)
        if csv_content is None:
            raise RuntimeError(f"Recuperation CSV echouee pour {dataset_id}.")

        csv_size = len(csv_content)
        if csv_size == 0:
            raise RuntimeError(f"CSV vide recupere pour {dataset_id}.")

        if BUCKET_NAME != bucket_name:
            raise RuntimeError(
                f"Bucket inattendu: '{BUCKET_NAME}' (attendu: '{bucket_name}')."
            )
        hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        hook.upload(
            bucket_name=bucket_name,
            object_name=f"{dataset_id}.csv",
            data=csv_content,
        )

    @task(task_id="transfer_csv_to_bigquery")
    def transfer_csv_from_bucket_to_bigquery(file_prefix: str) -> None:
        _run_transfer(file_prefix=file_prefix, gcp_conn_id=GCP_CONN_ID)

    check_bucket_connection_task: Any = check_bucket_connection()
    ingest_csv_to_bucket_task: Any = ingest_csv_to_bucket(
        bucket_name=check_bucket_connection_task,
        dataset_id=DATASET_ID,
    )
    transfer_csv_from_bucket_to_bigquery_task: Any = (
        transfer_csv_from_bucket_to_bigquery(file_prefix=FILE_PREFIX)
    )

    DBT_DIR = "../../dbt"

    dbt_eco2mix_regional_tr = BashOperator(
        task_id="dbt_eco2mix_regional_tr",
        bash_command=f"""
        cd {DBT_DIR} &&
        dbt run --select reg_tr_agre_j --target prod &&
        dbt run --select reg_tr_predi --target prod
        """,
    )

    (
        check_bucket_connection_task
        >> ingest_csv_to_bucket_task
        >> transfer_csv_from_bucket_to_bigquery_task
        >> dbt_eco2mix_regional_tr
    )


dag = dag_eco2mix_regional_tr()
