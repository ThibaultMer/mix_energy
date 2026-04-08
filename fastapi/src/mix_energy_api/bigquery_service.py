from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Sequence

from .config import Settings
from .schemas import FilterClause


class BigQueryServiceError(RuntimeError):
    """Base error for the dataset service."""


class UnknownTableError(BigQueryServiceError):
    """Raised when the requested table does not exist in the dataset."""


class UnknownColumnError(BigQueryServiceError):
    """Raised when the requested column does not exist in the table schema."""


class InvalidFilterError(BigQueryServiceError):
    """Raised when a filter cannot be converted to a safe SQL clause."""


@dataclass(frozen=True)
class ColumnMetadata:
    name: str
    field_type: str
    mode: str


@dataclass(frozen=True)
class TableMetadata:
    name: str
    table_type: str
    row_count: int | None
    columns: tuple[ColumnMetadata, ...]


def _import_bigquery_dependencies() -> tuple[Any, Any]:
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
    except ImportError as exc:  # pragma: no cover - only hit on missing dependency
        raise RuntimeError(
            "google-cloud-bigquery and google-auth must be installed to run the API"
        ) from exc
    return bigquery, service_account


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    raise InvalidFilterError(f"Cannot coerce {value!r} to bool")


def _coerce_scalar_value(field_type: str, value: Any) -> Any:
    normalized_type = field_type.upper()
    if value is None:
        return None
    if normalized_type in {"STRING", "BYTES", "JSON"}:
        return str(value)
    if normalized_type in {"INTEGER", "INT64"}:
        return int(value)
    if normalized_type in {"FLOAT", "FLOAT64"}:
        return float(value)
    if normalized_type in {"NUMERIC", "BIGNUMERIC"}:
        return Decimal(str(value))
    if normalized_type == "BOOL":
        return _coerce_bool(value)
    if normalized_type == "DATE":
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        return date.fromisoformat(str(value))
    if normalized_type == "DATETIME":
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        parsed_value = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed_value.replace(tzinfo=None)
    if normalized_type == "TIMESTAMP":
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        parsed_value = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return (
            parsed_value
            if parsed_value.tzinfo is not None
            else parsed_value.replace(tzinfo=UTC)
        )
    if normalized_type == "TIME":
        return str(value)
    return value


def _coerce_query_parameter(
    bigquery: Any, name: str, field_type: str, value: Any
) -> Any:
    normalized_type = field_type.upper()
    coerced_value = _coerce_scalar_value(normalized_type, value)
    if normalized_type in {"NUMERIC", "BIGNUMERIC"}:
        return bigquery.ScalarQueryParameter(name, normalized_type, coerced_value)
    if normalized_type in {"DATE", "DATETIME", "TIMESTAMP"}:
        return bigquery.ScalarQueryParameter(name, normalized_type, coerced_value)
    if normalized_type == "BOOL":
        return bigquery.ScalarQueryParameter(name, normalized_type, coerced_value)
    if normalized_type in {
        "INTEGER",
        "INT64",
        "FLOAT",
        "FLOAT64",
        "STRING",
        "BYTES",
        "JSON",
        "TIME",
    }:
        return bigquery.ScalarQueryParameter(name, normalized_type, coerced_value)
    return bigquery.ScalarQueryParameter(name, "STRING", str(coerced_value))


class BigQueryDatasetService:
    def __init__(self, settings: Settings, client: Any):
        self.settings = settings
        self.client = client
        self._tables: dict[str, TableMetadata] = {}

    @classmethod
    def create(cls, settings: Settings) -> "BigQueryDatasetService":
        bigquery, service_account = _import_bigquery_dependencies()
        credentials_path = settings.credentials_path
        if not credentials_path.exists():
            raise FileNotFoundError(f"Credential file not found: {credentials_path}")

        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path)
        )
        client = bigquery.Client(project=settings.project_id, credentials=credentials)
        service = cls(settings=settings, client=client)
        service.refresh_tables()
        return service

    @property
    def dataset_fqn(self) -> str:
        return f"{self.settings.project_id}.{self.settings.dataset_id}"

    def refresh_tables(self) -> None:
        self._tables.clear()
        table_iterator = self.client.list_tables(self.dataset_fqn)
        for table_ref in table_iterator:
            table_name = getattr(table_ref, "table_id", None) or getattr(
                table_ref, "table_name", None
            )
            if not table_name:
                continue
            if not self.settings.include_hidden_tables and table_name.startswith("_"):
                continue

            table = self.client.get_table(f"{self.dataset_fqn}.{table_name}")
            columns = tuple(
                ColumnMetadata(
                    name=field.name,
                    field_type=field.field_type,
                    mode=field.mode,
                )
                for field in table.schema
            )
            self._tables[_normalize_name(table_name)] = TableMetadata(
                name=table_name,
                table_type=getattr(table, "table_type", "TABLE"),
                row_count=getattr(table, "num_rows", None),
                columns=columns,
            )

    def list_tables(self) -> list[str]:
        return sorted([table.name for table in self._tables.values()])

    def get_table_columns(self, table_name: str) -> list[dict[str, Any]]:
        table = self.get_table(table_name)
        return [
            {
                "name": column.name,
                "field_type": column.field_type,
                "mode": column.mode,
            }
            for column in table.columns
        ]

    def get_table(self, table_name: str) -> TableMetadata:
        table = self._tables.get(_normalize_name(table_name))
        if table is None:
            raise UnknownTableError(
                f"Table '{table_name}' was not found in dataset {self.dataset_fqn}"
            )
        return table

    def _column_lookup(self, table: TableMetadata) -> dict[str, ColumnMetadata]:
        return {_normalize_name(column.name): column for column in table.columns}

    def _resolve_columns(
        self, table: TableMetadata, requested_columns: Sequence[str] | None
    ) -> list[ColumnMetadata]:
        column_lookup = self._column_lookup(table)
        if not requested_columns:
            return list(table.columns)

        resolved_columns: list[ColumnMetadata] = []
        missing_columns: list[str] = []
        for column_name in requested_columns:
            column = column_lookup.get(_normalize_name(column_name))
            if column is None:
                missing_columns.append(column_name)
                continue
            resolved_columns.append(column)

        if missing_columns:
            raise UnknownColumnError(
                f"Unknown columns for table {table.name}: {', '.join(missing_columns)}"
            )
        return resolved_columns

    def _resolve_filter(
        self, table: TableMetadata, filter_clause: FilterClause, index: int
    ) -> tuple[str, list[Any]]:
        column_lookup = self._column_lookup(table)
        column = column_lookup.get(_normalize_name(filter_clause.field))
        if column is None:
            raise UnknownColumnError(
                f"Unknown column '{filter_clause.field}' for table {table.name}"
            )

        parameter_name = f"filter_{index}"
        field_name = f"`{column.name}`"

        if filter_clause.operator == "is_null":
            return f"{field_name} IS NULL", []
        if filter_clause.operator == "not_null":
            return f"{field_name} IS NOT NULL", []

        bigquery = _import_bigquery_dependencies()[0]

        if filter_clause.operator == "contains":
            if filter_clause.value is None:
                raise InvalidFilterError(
                    f"Filter '{filter_clause.field}' requires a value for operator contains"
                )
            return (
                f"LOWER(CAST({field_name} AS STRING)) LIKE CONCAT('%', LOWER(@{parameter_name}), '%')",
                [
                    _coerce_query_parameter(
                        bigquery,
                        parameter_name,
                        "STRING",
                        filter_clause.value,
                    )
                ],
            )

        if filter_clause.operator == "in":
            if not isinstance(filter_clause.value, Sequence) or isinstance(
                filter_clause.value, (str, bytes)
            ):
                raise InvalidFilterError(
                    f"Filter '{filter_clause.field}' requires a list value for operator in"
                )
            coerced_values = [
                _coerce_scalar_value(column.field_type, value)
                for value in filter_clause.value
            ]
            return (
                f"{field_name} IN UNNEST(@{parameter_name})",
                [
                    bigquery.ArrayQueryParameter(
                        parameter_name, column.field_type.upper(), coerced_values
                    )
                ],
            )

        if filter_clause.value is None:
            raise InvalidFilterError(
                f"Filter '{filter_clause.field}' requires a value for operator {filter_clause.operator}"
            )

        operator_map = {
            "eq": "=",
            "ne": "!=",
            "lt": "<",
            "lte": "<=",
            "gt": ">",
            "gte": ">=",
        }
        sql_operator = operator_map.get(filter_clause.operator)
        if sql_operator is None:
            raise InvalidFilterError(
                f"Unsupported operator '{filter_clause.operator}' for column {column.name}"
            )

        return (
            f"{field_name} {sql_operator} @{parameter_name}",
            [
                _coerce_query_parameter(
                    bigquery,
                    parameter_name,
                    column.field_type,
                    filter_clause.value,
                )
            ],
        )

    def query_table(
        self,
        table_name: str,
        *,
        columns: Sequence[str] | None = None,
        filters: Sequence[FilterClause] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        table = self.get_table(table_name)
        requested_columns = self._resolve_columns(table, columns)
        selected_column_names = [column.name for column in requested_columns]

        bigquery = _import_bigquery_dependencies()[0]
        query_parameters: list[Any] = []
        where_clauses: list[str] = []

        try:
            for index, filter_clause in enumerate(filters or []):
                clause_sql, clause_parameters = self._resolve_filter(
                    table, filter_clause, index
                )
                where_clauses.append(clause_sql)
                query_parameters.extend(clause_parameters)
        except (ValueError, TypeError) as exc:
            raise BigQueryServiceError(
                f"Invalid filter value for table '{table.name}': {exc}"
            ) from exc

        safe_limit = (
            self.settings.default_limit
            if limit is None
            else max(1, min(limit, self.settings.max_limit))
        )
        query_parameters.append(
            bigquery.ScalarQueryParameter("limit_value", "INT64", safe_limit)
        )

        select_columns_sql = ", ".join(f"`{name}`" for name in selected_column_names)
        query_sql = (
            f"SELECT {select_columns_sql} FROM `{self.dataset_fqn}.{table.name}`"
        )
        if where_clauses:
            query_sql += " WHERE " + " AND ".join(where_clauses)
        query_sql += " LIMIT @limit_value"

        try:
            query_job_config = bigquery.QueryJobConfig(
                query_parameters=query_parameters
            )
            query_job = self.client.query(query_sql, job_config=query_job_config)
            rows = [dict(row) for row in query_job.result()]
        except Exception as exc:
            raise BigQueryServiceError(
                f"BigQuery query failed for table '{table.name}': {exc}"
            ) from exc

        return {
            "project_id": self.settings.project_id,
            "dataset_id": self.settings.dataset_id,
            "table_name": table.name,
            "selected_columns": selected_column_names,
            "filters": [filter_clause.model_dump() for filter_clause in filters or []],
            "limit": safe_limit,
            "row_count": len(rows),
            "rows": rows,
        }
