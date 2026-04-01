from google.cloud import storage
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# CONFIG
PROJECT_ID = "your-project-id"
DATASET_ID = "your_dataset"
BUCKET_NAME = "your-bucket-name"

# Clients
storage_client = storage.Client()
bq_client = bigquery.Client(project=PROJECT_ID)


def table_exists(table_id):
    try:
        bq_client.get_table(table_id)
        return True
    except NotFound:
        return False


def create_table_from_csv(table_id, uri):
    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,  # si header
        write_disposition=bigquery.WriteDisposition.WRITE_EMPTY,
    )

    load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)

    load_job.result()
    print(f"✅ Table créée et chargée: {table_id}")


def load_into_existing_table(table_id, uri):
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)

    load_job.result()
    print(f"➕ Données ajoutées à: {table_id}")


def main():
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs()

    for blob in blobs:
        if blob.name.endswith(".csv"):
            table_name = blob.name.split("/")[-1].replace(".csv", "")
            table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
            uri = f"gs://{BUCKET_NAME}/{blob.name}"

            print(f"📂 Traitement: {blob.name} → {table_name}")

            if not table_exists(table_id):
                create_table_from_csv(table_id, uri)
            else:
                load_into_existing_table(table_id, uri)


if __name__ == "__main__":
    main()
