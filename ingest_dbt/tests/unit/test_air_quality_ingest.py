from datetime import date

from mix_energy import air_quality_ingest as ingest


class DummyBlob:
    def __init__(self):
        self.uploaded = None

    def upload_from_string(self, data):
        self.uploaded = data


class DummyBucket:
    def __init__(self):
        self.blobs = {}

    def blob(self, name):
        blob = DummyBlob()
        self.blobs[name] = blob
        return blob


class FixedDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 4, 3)


def test_save_air_quality_to_bucket_uploads_csv():
    bucket = DummyBucket()
    features = [
        {
            "properties": {
                "code_insee": "75056",
                "libelle_zone": "Paris",
                "valeur": 2,
            }
        }
    ]

    saved = ingest.save_air_quality_to_bucket(features, bucket)

    assert saved is True
    assert "air_quality_daily.csv" in bucket.blobs
    assert bucket.blobs["air_quality_daily.csv"].uploaded.startswith(b"\xef\xbb\xbf")
    assert bucket.blobs["air_quality_daily.csv"].uploaded.endswith(
        b"code_insee,libelle_zone,valeur\r\n75056,Paris,2\r\n"
    )


def test_save_air_quality_to_bucket_returns_false_for_empty_features():
    bucket = DummyBucket()

    saved = ingest.save_air_quality_to_bucket([], bucket)

    assert saved is False
    assert bucket.blobs == {}


def test_run_ingestion_calls_api_connects_bucket_and_uploads(monkeypatch):
    called = {"api": None, "bucket": False, "upload": None}

    def fake_get_atmo_index(
        code_insee, date_histo, aasqa, date_jour=None, jwt_token=None
    ):
        called["api"] = (code_insee, date_histo, aasqa, date_jour, jwt_token)
        return {"features": [{"properties": {"value": 1}}]}

    def fake_connect_to_bucket():
        called["bucket"] = True
        return DummyBucket()

    def fake_upload_data_in_bucket(bucket, data, dataset):
        called["upload"] = (bucket, data, dataset)

    monkeypatch.setattr(ingest, "get_atmo_index", fake_get_atmo_index)
    monkeypatch.setattr(ingest, "get_jwt_token", lambda: "token-123")
    monkeypatch.setattr(ingest, "connect_to_bucket", fake_connect_to_bucket)
    monkeypatch.setattr(ingest, "upload_data_in_bucket", fake_upload_data_in_bucket)

    ingest.run_ingestion("2026-04-03")

    assert called["api"] == ("", "", "", "2026-04-03", "token-123")
    assert called["bucket"] is True
    assert called["upload"][2] == "air_quality_daily"
    assert called["upload"][1].startswith(b"\xef\xbb\xbf")
    assert called["upload"][1].endswith(b"value\r\n1\r\n")


def test_run_ingestion_no_data_does_not_connect_bucket(monkeypatch):
    called = {"bucket": False, "upload": False}

    monkeypatch.setattr(
        ingest,
        "get_atmo_index",
        lambda code_insee, date_histo, aasqa, date_jour=None, jwt_token=None: None,
    )
    monkeypatch.setattr(ingest, "get_jwt_token", lambda: "token-123")

    def fake_connect_to_bucket():
        called["bucket"] = True
        return DummyBucket()

    def fake_upload_data_in_bucket(*args, **kwargs):
        called["upload"] = True

    monkeypatch.setattr(ingest, "connect_to_bucket", fake_connect_to_bucket)
    monkeypatch.setattr(ingest, "upload_data_in_bucket", fake_upload_data_in_bucket)

    ingest.run_ingestion("2026-04-03")

    assert called["bucket"] is False
    assert called["upload"] is False


def test_run_ingestion_bucket_failure_skips_upload(monkeypatch):
    called = {"upload": False}

    monkeypatch.setattr(
        ingest,
        "get_atmo_index",
        lambda code_insee, date_histo, aasqa, date_jour=None, jwt_token=None: {
            "features": [{"properties": {"value": 1}}]
        },
    )
    monkeypatch.setattr(ingest, "get_jwt_token", lambda: "token-123")
    monkeypatch.setattr(ingest, "connect_to_bucket", lambda: None)

    def fake_upload_data_in_bucket(*args, **kwargs):
        called["upload"] = True

    monkeypatch.setattr(ingest, "upload_data_in_bucket", fake_upload_data_in_bucket)

    ingest.run_ingestion("2026-04-03")

    assert called["upload"] is False


def test_init_ingestion_uploads_one_csv_per_city(monkeypatch):
    called = {"api": [], "bucket": 0, "upload": []}
    cities = {
        "paris": {"insee_commune": "75056", "code_aasqa": 11},
        "lyon": {"insee_commune": "69123", "code_aasqa": 84},
    }

    monkeypatch.setattr(ingest, "CITIES", cities)
    monkeypatch.setattr(ingest, "date", FixedDate)

    def fake_get_atmo_index(
        code_insee, date_histo, aasqa, date_jour=None, jwt_token=None
    ):
        called["api"].append((code_insee, date_histo, aasqa, date_jour, jwt_token))
        return {"features": [{"properties": {"value": 1}}]}

    def fake_connect_to_bucket():
        called["bucket"] += 1
        return DummyBucket()

    def fake_upload_data_in_bucket(bucket, data, dataset):
        called["upload"].append((data, dataset))

    monkeypatch.setattr(ingest, "get_atmo_index", fake_get_atmo_index)
    monkeypatch.setattr(ingest, "get_jwt_token", lambda: "token-123")
    monkeypatch.setattr(ingest, "connect_to_bucket", fake_connect_to_bucket)
    monkeypatch.setattr(ingest, "upload_data_in_bucket", fake_upload_data_in_bucket)

    ingest.init_ingestion()

    assert called["api"] == [
        ("75056", "2026-03-03", "11", "2026-04-03", "token-123"),
        ("69123", "2026-03-03", "84", "2026-04-03", "token-123"),
    ]
    assert called["bucket"] == 1
    assert called["upload"] == [
        (b"\xef\xbb\xbfvalue\r\n1\r\n", "air_quality_paris"),
        (b"\xef\xbb\xbfvalue\r\n1\r\n", "air_quality_lyon"),
    ]
