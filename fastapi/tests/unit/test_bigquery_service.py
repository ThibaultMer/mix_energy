from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mix_energy_api.bigquery_service import BigQueryDatasetService
from mix_energy_api.config import Settings
from mix_energy_api.schemas import FilterClause


@dataclass
class FakeField:
    name: str
    field_type: str
    mode: str = "NULLABLE"


@dataclass
class FakeTable:
    schema: tuple[FakeField, ...]
    table_type: str = "TABLE"
    num_rows: int = 0


@dataclass
class FakeTableRef:
    table_id: str


class FakeQueryJob:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class FakeClient:
    def __init__(self):
        self.queries = []

    def list_tables(self, dataset_fqn):
        return [FakeTableRef("daily_stats"), FakeTableRef("_loaded_files")]

    def get_table(self, table_fqn):
        return FakeTable(
            schema=(
                FakeField("day", "DATE"),
                FakeField("region", "STRING"),
                FakeField("value", "FLOAT64"),
            ),
            table_type="TABLE",
            num_rows=12,
        )

    def query(self, sql, job_config=None):
        self.queries.append((sql, job_config))
        return FakeQueryJob([{"day": "2024-01-01", "region": "FR", "value": 1.2}])


def _build_service(include_hidden_tables: bool = False) -> BigQueryDatasetService:
    settings = Settings(
        project_id="mix-energie-gcp",
        dataset_id="prod_mix_energie",
        credentials_path=Path("/tmp/fake.json"),
        include_hidden_tables=include_hidden_tables,
    )
    service = BigQueryDatasetService(settings=settings, client=FakeClient())
    service.refresh_tables()
    return service


def test_refresh_tables_excludes_hidden_tables_by_default():
    service = _build_service()

    tables = service.list_tables()

    assert tables == ["daily_stats"]


def test_get_table_columns():
    service = _build_service()

    columns = service.get_table_columns("daily_stats")

    assert len(columns) == 3
    assert columns[0]["name"] == "day"
    assert columns[1]["name"] == "region"
    assert columns[2]["name"] == "value"


def test_query_table_builds_safe_sql_and_filters():
    service = _build_service()

    result = service.query_table(
        "daily_stats",
        columns=["day", "region"],
        filters=[
            FilterClause(field="region", operator="eq", value="FR"),
            FilterClause(field="value", operator="gte", value=1.0),
        ],
        limit=25,
    )

    sql, job_config = service.client.queries[0]
    assert (
        "SELECT `day`, `region` FROM `mix-energie-gcp.prod_mix_energie.daily_stats`"
        in sql
    )
    assert "WHERE `region` = @filter_0 AND `value` >= @filter_1" in sql
    assert "LIMIT @limit_value" in sql
    assert result["row_count"] == 1
    assert result["selected_columns"] == ["day", "region"]
    assert job_config.query_parameters[-1].name == "limit_value"


def test_query_table_rejects_unknown_columns():
    service = _build_service()

    try:
        service.query_table("daily_stats", columns=["bad_column"])
    except Exception as exc:
        assert "Unknown columns" in str(exc)
    else:
        raise AssertionError("Unknown columns should fail")
