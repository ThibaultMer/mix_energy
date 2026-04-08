from google.cloud import bigquery, storage

from mix_energy.bucket_to_bigquery import PROJECT_ID, run_transfer as _run_transfer


def _build_clients_from_airflow_connection(gcp_conn_id: str):
    from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
    from airflow.providers.google.cloud.hooks.gcs import GCSHook

    bq_hook = BigQueryHook(gcp_conn_id=gcp_conn_id, use_legacy_sql=False)
    gcs_hook = GCSHook(gcp_conn_id=gcp_conn_id)

    return bq_hook.get_client(project_id=PROJECT_ID), gcs_hook.get_conn()


def run_transfer(
    file_prefix: str | None = None,
    gcp_conn_id: str = "google_cloud_default",
    bq_client: bigquery.Client | None = None,
    gcs_client: storage.Client | None = None,
):
    if bq_client is None or gcs_client is None:
        bq_client, gcs_client = _build_clients_from_airflow_connection(
            gcp_conn_id=gcp_conn_id
        )

    _run_transfer(
        file_prefix=file_prefix,
        bq_client=bq_client,
        gcs_client=gcs_client,
    )
