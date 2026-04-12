from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from airflow.sdk import dag, task
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.timetables.trigger import MultipleCronTriggerTimetable

from predict.train import train

GCP_CONN_ID = "google_cloud_default"
DATASET_ID = os.getenv("DATASET_ID", "prod_mix_energie")
PROJECT_ID = os.getenv("PROJECT_ID")


@dag(
    dag_id="dag_train_model",
    description="Entraine les modèles de machine learning pour la prédiction de consommation d'énergie.",
    start_date=datetime(2026, 1, 1),
    schedule=MultipleCronTriggerTimetable(
        "10 12 2 * 1-5",
        "10 12 2 * 1",
        "10 12 2 * 1",
        timezone="Europe/Paris",
    ),
    catchup=False,
    tags=["ml-model", "training"],
)
def dag_train_model():
    @task(task_id="check_bigquery_connection")
    def check_bigquery_connection() -> None:
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID, use_legacy_sql=False)
        print("Check Bigquery connection")

        try:
            nat_tr_exist = bq_hook.table_exists(
                project_id=PROJECT_ID,
                dataset_id=f"{DATASET_ID}_gold",
                table_id="nat_tr_predi",
            )
            reg_tr_exist = bq_hook.table_exists(
                project_id=PROJECT_ID,
                dataset_id=f"{DATASET_ID}_gold",
                table_id="reg_tr_predi",
            )
            if not nat_tr_exist or not reg_tr_exist:
                raise RuntimeError("GOLD Tables not available")
        except Exception as exc:
            raise RuntimeError("Connexion BigQuery impossible.") from exc

    @task(task_id="train_reg_model")
    def train_reg_model() -> None:
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID, use_legacy_sql=False)
        bq_client = bq_hook.get_client(project_id=PROJECT_ID)

        try:
            train(bqclient=bq_client, is_national=True)
        except Exception as exc:
            raise RuntimeError(
                "Echec de l'entrainement du modèle pour les régions"
            ) from exc

    @task(task_id="train_nat_model")
    def train_nat_model() -> None:
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID, use_legacy_sql=False)
        bq_client = bq_hook.get_client(project_id=PROJECT_ID)

        try:
            train(bqclient=bq_client, is_national=False)
        except Exception as exc:
            raise RuntimeError(
                "Echec de l'entrainement du modèle pour les régions"
            ) from exc

    check_bigquery_connection_task: Any = check_bigquery_connection()
    train_reg_model_task: Any = train_reg_model()
    train_nat_model_task: Any = train_nat_model()

    (check_bigquery_connection_task >> train_reg_model_task >> train_nat_model_task)


dag = dag_train_model()
