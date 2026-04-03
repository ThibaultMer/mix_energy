import pandas as pd

from mix_energy import bigquery_schema_generator as generator


def test_create_generic_schema_maps_types_and_names():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-04-01", "2026-04-02"]),
            "time_stamp": pd.to_datetime(
                ["2026-04-01T00:00:00", "2026-04-01T01:00:00"]
            ),
            "value": [1.2, 2.4],
            "label": ["a", "b"],
        }
    )

    schema = generator.create_generic_schema(df)
    by_name = {field.name: field.field_type for field in schema}

    assert by_name["date"] == "DATE"
    assert by_name["time_stamp"] == "TIMESTAMP"
    assert by_name["value"] == "FLOAT"
    assert by_name["label"] == "STRING"


def test_generate_all_schemas_returns_filename_keyed_dict(monkeypatch):
    df = pd.DataFrame({"col1": [1, 2], "col2": ["x", "y"]})

    def fake_read_csv_from_gcs(
        gcs_client, bucket_name, blob_name, sample_rows, delimiter
    ):
        assert bucket_name == "my-bucket"
        assert sample_rows == 200
        assert delimiter == ";"
        return df

    monkeypatch.setattr(generator, "read_csv_from_gcs", fake_read_csv_from_gcs)

    schema_dict = generator.generate_all_schemas(
        gcs_client=object(),
        bucket_name="my-bucket",
        blob_names=["a/source.csv", "b/source.csv"],
        sample_rows=200,
    )

    assert list(schema_dict.keys()) == ["source.csv"]
    assert schema_dict["source.csv"] is not None
    assert len(schema_dict["source.csv"]) == 2


def test_generate_all_schemas_puts_none_when_inference_fails(monkeypatch):
    def fake_read_csv_from_gcs(
        gcs_client, bucket_name, blob_name, sample_rows, delimiter
    ):
        raise RuntimeError("boom")

    monkeypatch.setattr(generator, "read_csv_from_gcs", fake_read_csv_from_gcs)

    schema_dict = generator.generate_all_schemas(
        gcs_client=object(),
        bucket_name="my-bucket",
        blob_names=["folder/a.csv"],
        sample_rows=100,
    )

    assert schema_dict == {"a.csv": None}


def test_get_csv_delimiter_for_filename_routes_prefixes():
    assert generator.get_csv_delimiter_for_filename("meteo_paris.csv") == ","
    assert generator.get_csv_delimiter_for_filename("air_quality.csv") == ","
    assert generator.get_csv_delimiter_for_filename("eco2mix-national.csv") == ";"
    assert generator.get_csv_delimiter_for_filename("other.csv") == ";"


def test_create_bigquery_schema_for_file_dispatches_by_prefix(monkeypatch):
    df = pd.DataFrame({"x": [1]})

    monkeypatch.setattr(generator, "create_eco2mix_schema", lambda _df: ["eco2mix"])
    monkeypatch.setattr(generator, "create_meteo_schema", lambda _df: ["meteo"])
    monkeypatch.setattr(
        generator, "create_air_quality_schema", lambda _df: ["air_quality"]
    )
    monkeypatch.setattr(generator, "create_generic_schema", lambda _df: ["generic"])

    assert generator.create_bigquery_schema_for_file("eco2mix-national.csv", df) == [
        "eco2mix"
    ]
    assert generator.create_bigquery_schema_for_file("meteo_paris.csv", df) == ["meteo"]
    assert generator.create_bigquery_schema_for_file("air_quality.csv", df) == [
        "air_quality"
    ]
    assert generator.create_bigquery_schema_for_file("other_dataset.csv", df) == [
        "generic"
    ]


def test_create_meteo_schema_falls_back_to_generic_rules_for_unknown_columns():
    df = pd.DataFrame({"value": [1.2, 2.4]})

    schema = generator.create_meteo_schema(df)

    assert schema[0].name == "value"
    assert schema[0].field_type == "FLOAT"


def test_create_air_quality_schema_handles_insee_as_string():
    df = pd.DataFrame({"code_insee": ["75056", "13055"]})

    schema = generator.create_air_quality_schema(df)

    assert schema[0].name == "code_insee"
    assert schema[0].field_type == "STRING"
