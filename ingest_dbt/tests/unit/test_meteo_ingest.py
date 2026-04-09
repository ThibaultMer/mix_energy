import pandas as pd
import requests
import pytest

from mix_energy.meteo_ingest import (
    get_meteo_forecast,
    json_to_dataframe,
    save_meteo_to_csv,
)


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.url = "https://api.open-meteo.com/v1/forecast?latitude=48.8534"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_get_meteo_forecast_success(monkeypatch):
    payload = {"hourly": {"time": ["2026-03-31T00:00"], "temperature_2m": [14.2]}}

    def fake_get(url, params):
        assert "forecast" in url
        assert params["latitude"] == 48.8534
        return DummyResponse(payload)

    monkeypatch.setattr("requests.get", fake_get)

    result = get_meteo_forecast(48.8534, 2.3488, 10, 1)

    assert result == payload


def test_get_meteo_forecast_request_error_returns_empty_dict(monkeypatch):
    def fake_get(url, params):
        raise requests.exceptions.RequestException("network down")

    monkeypatch.setattr("requests.get", fake_get)

    result = get_meteo_forecast(48.8534, 2.3488, 10, 1)

    assert result == {}


def test_json_to_dataframe_converts_time_column_to_datetime():
    meteo_data = {
        "hourly": {
            "time": ["2026-03-31T00:00", "2026-03-31T01:00"],
            "temperature_2m": [13.4, 12.8],
        }
    }

    df = json_to_dataframe(meteo_data)

    assert list(df.columns) == ["time", "temperature_2m"]
    assert pd.api.types.is_datetime64_any_dtype(df["time"])
    assert len(df) == 2


def test_json_to_dataframe_empty_payload_returns_empty_dataframe():
    df = json_to_dataframe({})

    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_save_meteo_to_csv_uploads_expected_dataset(monkeypatch):
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(["2026-03-31T00:00"]),
            "temperature_2m": [15.0],
        }
    )

    fake_bucket = object()
    captured = {}

    def fake_connect_to_bucket():
        return fake_bucket

    def fake_upload_data_in_bucket(bucket, data, dataset):
        captured["bucket"] = bucket
        captured["data"] = data
        captured["dataset"] = dataset

    monkeypatch.setattr(
        "mix_energy.meteo_ingest.connect_to_bucket", fake_connect_to_bucket
    )
    monkeypatch.setattr(
        "mix_energy.meteo_ingest.upload_data_in_bucket",
        fake_upload_data_in_bucket,
    )

    save_meteo_to_csv(df, "paris")

    assert captured["bucket"] is fake_bucket
    assert captured["dataset"] == "meteo_paris"
    assert "temperature_2m" in captured["data"]
    assert "15.0" in captured["data"]


def test_save_meteo_to_csv_raises_when_bucket_unavailable(monkeypatch):
    df = pd.DataFrame(
        {"time": pd.to_datetime(["2026-03-31T00:00"]), "temperature_2m": [15.0]}
    )

    monkeypatch.setattr("mix_energy.meteo_ingest.connect_to_bucket", lambda: None)

    with pytest.raises(RuntimeError, match="Impossible de se connecter au bucket GCP"):
        save_meteo_to_csv(df, "paris")
