from pathlib import Path

import pandas as pd
import requests

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


def test_save_meteo_to_csv_writes_expected_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("data/meteo").mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        {
            "time": pd.to_datetime(["2026-03-31T00:00"]),
            "temperature_2m": [15.0],
        }
    )

    save_meteo_to_csv(df, "paris")

    output_file = Path("data/meteo/meteo_paris.csv")
    assert output_file.exists()

    saved_df = pd.read_csv(output_file)
    assert list(saved_df.columns) == ["time", "temperature_2m"]
    assert len(saved_df) == 1

    output_file.unlink()
    assert not output_file.exists()
