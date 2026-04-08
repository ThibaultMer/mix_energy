from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


FilterOperator = Literal[
    "eq",
    "ne",
    "lt",
    "lte",
    "gt",
    "gte",
    "contains",
    "in",
    "is_null",
    "not_null",
]


class FilterClause(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str = Field(..., min_length=1)
    operator: FilterOperator
    value: Any | list[Any] | None = None


class ColumnInfo(BaseModel):
    name: str
    field_type: str
    mode: str


class TableInfo(BaseModel):
    name: str
    table_type: str
    row_count: int | None = None
    columns: list[ColumnInfo]


class DatasetOverview(BaseModel):
    project_id: str
    dataset_id: str
    tables: list[str]


class TableColumns(BaseModel):
    table_name: str
    columns: list[ColumnInfo]


class QueryResponse(BaseModel):
    project_id: str
    dataset_id: str
    table_name: str
    selected_columns: list[str]
    filters: list[FilterClause]
    limit: int
    row_count: int
    rows: list[dict[str, Any]]
