from google.cloud import bigquery

from mix_energy import bucket_to_bigquery as transfer


class _FakeBlob:
    def __init__(self, name: str):
        self.name = name


def test_filter_csv_blobs_by_filename_prefix_keeps_matching_files_only():
    blobs = [
        _FakeBlob("raw/eco2mix-national-cons-def.csv"),
        _FakeBlob("raw/eco2mix-national-tr.csv"),
        _FakeBlob("raw/air_quality_paris.csv"),
        _FakeBlob("raw/meteo_paris.csv"),
    ]

    filtered = transfer._filter_csv_blobs_by_filename_prefix(
        blobs, "eco2mix-national-cons"
    )

    assert [blob.name for blob in filtered] == ["raw/eco2mix-national-cons-def.csv"]


def test_run_transfer_filters_blob_names_before_bigquery_calls(monkeypatch):
    captured = {"schemas": None, "loads": None}

    monkeypatch.setattr(transfer, "PROJECT_ID", "project-x")
    monkeypatch.setattr(transfer, "DATASET_ID", "dataset-x")
    monkeypatch.setattr(transfer, "BUCKET_NAME", "bucket-x")
    monkeypatch.setattr(transfer, "PREFIX", "raw/")

    class _FakeCredentials:
        pass

    class _FakeBucket:
        def list_blobs(self, prefix=None):
            assert prefix == "raw/"
            return [
                _FakeBlob("raw/eco2mix-national-cons-def.csv"),
                _FakeBlob("raw/eco2mix-national-tr.csv"),
                _FakeBlob("raw/air_quality_paris.csv"),
            ]

    class _FakeGcsClient:
        def bucket(self, bucket_name):
            assert bucket_name == "bucket-x"
            return _FakeBucket()

    class _FakeBqClient:
        pass

    monkeypatch.setattr(
        transfer.service_account.Credentials,
        "from_service_account_file",
        lambda _path: _FakeCredentials(),
    )
    monkeypatch.setattr(transfer.bigquery, "Client", lambda **_kwargs: _FakeBqClient())
    monkeypatch.setattr(transfer.storage, "Client", lambda **_kwargs: _FakeGcsClient())

    def fake_generate_all_schemas(gcs_client, bucket_name, blob_names, sample_rows):
        captured["schemas"] = blob_names
        return {
            blob_name.split("/")[-1]: [bigquery.SchemaField("col", "STRING")]
            for blob_name in blob_names
        }

    def fake_load_all_from_schemas(bq_client, bucket_name, blob_names, schema_dict):
        captured["loads"] = blob_names

    monkeypatch.setattr(transfer, "generate_all_schemas", fake_generate_all_schemas)
    monkeypatch.setattr(transfer, "load_all_from_schemas", fake_load_all_from_schemas)

    transfer.run_transfer(file_prefix="eco2mix-national-cons")

    assert captured["schemas"] == ["raw/eco2mix-national-cons-def.csv"]
    assert captured["loads"] == ["raw/eco2mix-national-cons-def.csv"]
