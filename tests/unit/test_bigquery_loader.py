from google.cloud import bigquery

from mix_energy import bigquery_loader as loader


def test_load_all_from_schemas_init_branch_uses_histo_and_marks_init(monkeypatch):
    calls = {"load": [], "mark": [], "mark_init": []}

    def fake_load_csv_to_bigquery(
        bq_client,
        uri,
        table_id,
        schema=None,
        write_disposition=None,
        field_delimiter=None,
    ):
        calls["load"].append(
            (uri, table_id, schema, write_disposition, field_delimiter)
        )
        return True

    def fake_mark_file_as_loaded(client, filename):
        calls["mark"].append(filename)

    def fake_mark_file_as_initialized(client, filename):
        calls["mark_init"].append(filename)

    monkeypatch.setattr(loader, "get_initialized_files", lambda _client: set())
    monkeypatch.setattr(loader, "load_csv_to_bigquery", fake_load_csv_to_bigquery)
    monkeypatch.setattr(loader, "mark_file_as_loaded", fake_mark_file_as_loaded)
    monkeypatch.setattr(
        loader, "mark_file_as_initialized", fake_mark_file_as_initialized
    )

    schema = [bigquery.SchemaField("col", "STRING")]
    loader.load_all_from_schemas(
        bq_client=object(),
        bucket_name="bucket-x",
        blob_names=["x/file_a.csv"],
        schema_dict={"file_a.csv": schema},
    )

    assert len(calls["load"]) == 1
    assert calls["load"][0][0] == "gs://bucket-x/x/file_a.csv"
    assert calls["load"][0][1].endswith("file_a_histo")
    assert calls["load"][0][3] == bigquery.WriteDisposition.WRITE_APPEND
    assert calls["load"][0][4] == ";"
    assert calls["mark_init"] == ["x/file_a.csv"]
    assert calls["mark"] == ["x/file_a.csv"]


def test_load_all_from_schemas_post_init_uses_standard_table_and_truncate(monkeypatch):
    calls = {"load": [], "mark": [], "mark_init": []}

    def fake_load_csv_to_bigquery(
        bq_client,
        uri,
        table_id,
        schema=None,
        write_disposition=None,
        field_delimiter=None,
    ):
        calls["load"].append(
            (uri, table_id, schema, write_disposition, field_delimiter)
        )
        return True

    def fake_mark_file_as_loaded(client, filename):
        calls["mark"].append(filename)

    def fake_mark_file_as_initialized(client, filename):
        calls["mark_init"].append(filename)

    monkeypatch.setattr(
        loader, "get_initialized_files", lambda _client: {"x/file_b.csv"}
    )
    monkeypatch.setattr(loader, "load_csv_to_bigquery", fake_load_csv_to_bigquery)
    monkeypatch.setattr(loader, "mark_file_as_loaded", fake_mark_file_as_loaded)
    monkeypatch.setattr(
        loader, "mark_file_as_initialized", fake_mark_file_as_initialized
    )

    schema = [bigquery.SchemaField("col", "STRING")]
    loader.load_all_from_schemas(
        bq_client=object(),
        bucket_name="bucket-x",
        blob_names=["x/file_b.csv"],
        schema_dict={"file_b.csv": schema},
    )

    assert len(calls["load"]) == 1
    assert calls["load"][0][1].endswith("file_b")
    assert not calls["load"][0][1].endswith("file_b_histo")
    assert calls["load"][0][3] == bigquery.WriteDisposition.WRITE_TRUNCATE
    assert calls["load"][0][4] == ";"
    assert calls["mark_init"] == []
    assert calls["mark"] == ["x/file_b.csv"]


def test_load_all_from_schemas_retries_with_string_schema(monkeypatch):
    calls = {"load": [], "mark": []}

    def fake_load_csv_to_bigquery(
        bq_client,
        uri,
        table_id,
        schema=None,
        write_disposition=None,
        field_delimiter=None,
    ):
        calls["load"].append((schema, write_disposition, table_id, field_delimiter))
        return len(calls["load"]) > 1

    def fake_mark_file_as_loaded(client, filename):
        calls["mark"].append(filename)

    monkeypatch.setattr(loader, "get_initialized_files", lambda _client: set())
    monkeypatch.setattr(
        loader, "mark_file_as_initialized", lambda _client, _filename: None
    )

    monkeypatch.setattr(loader, "load_csv_to_bigquery", fake_load_csv_to_bigquery)
    monkeypatch.setattr(loader, "mark_file_as_loaded", fake_mark_file_as_loaded)

    original_schema = [
        bigquery.SchemaField("a", "INTEGER"),
        bigquery.SchemaField("b", "FLOAT"),
    ]

    loader.load_all_from_schemas(
        bq_client=object(),
        bucket_name="bucket-x",
        blob_names=["x/file_b.csv"],
        schema_dict={"file_b.csv": original_schema},
    )

    assert len(calls["load"]) == 2
    assert calls["load"][0][0] == original_schema
    assert all(field.field_type == "STRING" for field in calls["load"][1][0])
    assert calls["load"][0][1] == bigquery.WriteDisposition.WRITE_APPEND
    assert calls["load"][1][1] == bigquery.WriteDisposition.WRITE_APPEND
    assert calls["load"][0][2].endswith("file_b_histo")
    assert calls["load"][0][3] == ";"
    assert calls["mark"] == ["x/file_b.csv"]


def test_load_all_from_schemas_uses_comma_delimiter_for_meteo_and_air_quality(
    monkeypatch,
):
    calls = {"load": []}

    def fake_load_csv_to_bigquery(
        bq_client,
        uri,
        table_id,
        schema=None,
        write_disposition=None,
        field_delimiter=None,
    ):
        calls["load"].append((uri, field_delimiter))
        return True

    monkeypatch.setattr(loader, "get_initialized_files", lambda _client: set())
    monkeypatch.setattr(
        loader, "mark_file_as_initialized", lambda _client, _filename: None
    )
    monkeypatch.setattr(loader, "mark_file_as_loaded", lambda _client, _filename: None)
    monkeypatch.setattr(loader, "load_csv_to_bigquery", fake_load_csv_to_bigquery)

    schema = [bigquery.SchemaField("col", "STRING")]
    loader.load_all_from_schemas(
        bq_client=object(),
        bucket_name="bucket-x",
        blob_names=["x/meteo_paris.csv", "x/air_quality.csv", "x/eco2mix-national.csv"],
        schema_dict={
            "meteo_paris.csv": schema,
            "air_quality.csv": schema,
            "eco2mix-national.csv": schema,
        },
    )

    assert calls["load"][0][1] == ","
    assert calls["load"][1][1] == ","
    assert calls["load"][2][1] == ";"
