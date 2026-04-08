from __future__ import annotations

import json
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from .bigquery_service import (
    BigQueryDatasetService,
    BigQueryServiceError,
    InvalidFilterError,
    UnknownColumnError,
    UnknownTableError,
)
from .config import load_settings
from .schemas import DatasetOverview, FilterClause, QueryResponse, TableColumns


def _parse_columns(columns: str | None) -> list[str] | None:
    if not columns:
        return None
    if columns.strip() == "*":
        return None
    parsed_columns = [column.strip() for column in columns.split(",") if column.strip()]
    return parsed_columns or None


def _parse_filters(filters: str | None) -> list[FilterClause] | None:
    if not filters:
        return None

    try:
        payload = json.loads(filters)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400, detail="filters must be valid JSON"
        ) from exc

    if not isinstance(payload, list):
        raise HTTPException(status_code=400, detail="filters must be a JSON array")

    try:
        return [FilterClause.model_validate(item) for item in payload]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(
        title="Mix Energy Dataset API",
        version="0.1.0",
        description="Read-only BigQuery buffer for the Streamlit front-end.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        app.state.settings = settings
        app.state.service = BigQueryDatasetService.create(settings)

    def get_service(request: Request) -> BigQueryDatasetService:
        service = getattr(request.app.state, "service", None)
        if service is None:
            raise HTTPException(status_code=503, detail="BigQuery service is not ready")
        return service

    @app.get("/health")
    def health(request: Request) -> dict[str, str]:
        loaded_settings = getattr(request.app.state, "settings", settings)
        return {
            "status": "ok",
            "project_id": loaded_settings.project_id,
            "dataset_id": loaded_settings.dataset_id,
        }

    @app.get("/tables", response_model=DatasetOverview)
    def list_tables(
        service: BigQueryDatasetService = Depends(get_service),
    ) -> dict[str, Any]:
        return {
            "project_id": service.settings.project_id,
            "dataset_id": service.settings.dataset_id,
            "tables": service.list_tables(),
        }

    @app.get("/tables/{table_name}/columns", response_model=TableColumns)
    def get_table_columns(
        table_name: str,
        service: BigQueryDatasetService = Depends(get_service),
    ) -> dict[str, Any]:
        try:
            columns = service.get_table_columns(table_name)
            return {
                "table_name": table_name,
                "columns": columns,
            }
        except UnknownTableError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/tables/{table_name}", response_model=QueryResponse)
    def query_table(
        table_name: str,
        columns: str | None = Query(
            default=None, description="Comma-separated list of columns"
        ),
        filters: str | None = Query(
            default=None,
            description="JSON array of filter clauses, e.g. [{'field':'date','operator':'gte','value':'2024-01-01'}]",
        ),
        limit: int | None = Query(default=None, ge=1),
        service: BigQueryDatasetService = Depends(get_service),
    ) -> dict[str, Any]:
        parsed_columns = _parse_columns(columns)
        parsed_filters = _parse_filters(filters)

        try:
            return service.query_table(
                table_name,
                columns=parsed_columns,
                filters=parsed_filters,
                limit=limit,
            )
        except UnknownTableError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except UnknownColumnError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except InvalidFilterError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BigQueryServiceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
