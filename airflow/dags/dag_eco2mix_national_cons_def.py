from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from mix_energy.eco2mix_ingest import retrieve_csv as _retrieve_csv
from mix_energy.gcp_utils import connect_to_bucket, upload_data_in_bucket

DATASET_ID = "eco2mix-national-cons-def"


@dag(
    dag_id="dag_eco2mix_national_cons_def",
    description="Ingestion eco2mix national cons-def vers GCS.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["eco2mix", "ingestion"],
)
def dag_eco2mix_national_cons_def():
    @task(task_id="check_bucket_connection")
    def check_bucket_connection() -> str:
        bucket = connect_to_bucket()
        if bucket is None:
            raise RuntimeError("Connexion au bucket GCP impossible.")
        return bucket.name

    @task(task_id="ingest_csv_to_bucket")
    def ingest_csv_to_bucket(bucket_name: str, dataset_id: str) -> None:
        csv_content = _retrieve_csv(dataset_id=dataset_id)
        if csv_content is None:
            raise RuntimeError(f"Recuperation CSV echouee pour {dataset_id}.")

        csv_size = len(csv_content)
        if csv_size == 0:
            raise RuntimeError(f"CSV vide recupere pour {dataset_id}.")

        bucket = connect_to_bucket()
        if bucket is None:
            raise RuntimeError("Connexion au bucket GCP impossible.")
        if bucket.name != bucket_name:
            raise RuntimeError(
                f"Bucket inattendu: '{bucket.name}' (attendu: '{bucket_name}')."
            )

        upload_data_in_bucket(bucket, csv_content, dataset_id)

    check_bucket_connection_task = check_bucket_connection()
    ingest_csv_to_bucket_task = ingest_csv_to_bucket(
        bucket_name=check_bucket_connection_task,
        dataset_id=DATASET_ID,
    )

    check_bucket_connection_task >> ingest_csv_to_bucket_task


dag = dag_eco2mix_national_cons_def()
