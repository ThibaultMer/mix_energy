from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


DEFAULT_BASE_URL = "http://localhost:8888"


def _load_env_files() -> None:
    repo_root_env = Path(__file__).resolve().parents[2] / ".env"
    front_env = Path(__file__).resolve().parents[1] / ".env"

    if repo_root_env.exists():
        load_dotenv(repo_root_env, override=False)
    if front_env.exists():
        load_dotenv(front_env, override=False)

    load_dotenv(override=False)


@dataclass
class FastAPIClient:
    base_url: str
    timeout_seconds: int = 25
    per_call_limit: int = 1000

    @classmethod
    def from_environment(cls) -> "FastAPIClient":
        _load_env_files()
        base_url = os.getenv("FASTAPI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        timeout_seconds = int(os.getenv("FASTAPI_TIMEOUT_SECONDS", "25"))
        per_call_limit = int(os.getenv("FASTAPI_PAGE_LIMIT", "1000"))
        return cls(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            per_call_limit=per_call_limit,
        )

    def health(self) -> dict[str, Any]:
        return self._safe_get_json("/health")

    def get_table_columns(self, table_name: str) -> list[dict[str, Any]]:
        payload = self._safe_get_json(f"/tables/{table_name}/columns")
        return payload.get("columns", [])

    def query_table(
        self,
        table_name: str,
        *,
        filters: list[dict[str, Any]] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit or self.per_call_limit}
        if filters:
            params["filters"] = json.dumps(filters, ensure_ascii=False)

        return self._safe_get_json(f"/tables/{table_name}", params=params)

    def _safe_get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            response = exc.response
            status_code = response.status_code if response is not None else "unknown"
            response_text = ""
            if response is not None:
                try:
                    payload = response.json()
                    response_text = json.dumps(payload, ensure_ascii=False)
                except ValueError:
                    response_text = response.text

            raise RuntimeError(
                "FastAPI request failed with HTTP error. "
                f"path={path}, base_url={self.base_url}, status={status_code}, response={response_text}"
            ) from exc
        except requests.RequestException as exc:
            raise RuntimeError(
                "FastAPI request failed (network/timeout). Check FASTAPI_BASE_URL, API availability, and credentials. "
                f"path={path}, base_url={self.base_url}"
            ) from exc

    def _safe_post_json(self, path: str, params):
        try:
            response = requests.post(
                f"{self.base_url}{path}",
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            response = exc.response
            status_code = response.status_code if response is not None else "unknown"
            response_text = ""
            if response is not None:
                try:
                    payload = response.json()
                    response_text = json.dumps(payload, ensure_ascii=False)
                except ValueError:
                    response_text = response.text

            raise RuntimeError(
                "FastAPI request failed with HTTP error. "
                f"path={path}, base_url={self.base_url}, status={status_code}, response={response_text}"
            ) from exc
        except requests.RequestException as exc:
            raise RuntimeError(
                "FastAPI request failed (network/timeout). Check FASTAPI_BASE_URL, API availability, and credentials. "
                f"path={path}, base_url={self.base_url}"
            ) from exc

    def predict_national(self):
        next_conso = self._safe_post_json(path="/predict/national", params={})
        return next_conso

    def prediction_region(self, insee_code: int):
        params = {"code_insee_region": insee_code}
        next_conso = self._safe_post_json(path="/predict/region", params=params)
        return next_conso

    def _get_column_map(self, table_name: str) -> dict[str, dict[str, Any]]:
        return {
            str(col.get("name")): col
            for col in self.get_table_columns(table_name)
            if col.get("name")
        }

    def detect_date_field(self, table_name: str) -> tuple[str, str]:
        column_map = self._get_column_map(table_name)

        # Priority 1: canonical names that are truly date/time typed.
        for candidate in ("date", "datetime", "timestamp", "mois", "jour"):
            column = column_map.get(candidate)
            if column:
                field_type = str(column.get("field_type", "STRING")).upper()
                if field_type in {"DATE", "DATETIME", "TIMESTAMP"}:
                    return candidate, field_type

        # Priority 2: any column with a date/time type.
        for name, column in column_map.items():
            field_type = str(column.get("field_type", "")).upper()
            if field_type in {"DATE", "DATETIME", "TIMESTAMP"}:
                return name, field_type

        # Priority 3: fallback to common names even if numeric/string encoded.
        for candidate in ("date", "mois", "jour"):
            column = column_map.get(candidate)
            if column:
                return candidate, str(column.get("field_type", "STRING")).upper()

        raise ValueError(f"No date column found for table '{table_name}'")

    def detect_region_field(self, table_name: str) -> str:
        columns = {col.get("name") for col in self.get_table_columns(table_name)}
        if "libelle_region" in columns:
            return "libelle_region"
        if "region" in columns:
            return "region"
        raise ValueError(f"No region column found for table '{table_name}'")

    def load_rows_for_date_range(
        self,
        table_name: str,
        *,
        start_date: date,
        end_date: date,
        extra_filters: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        date_field, date_field_type = self.detect_date_field(table_name)
        rows: list[dict[str, Any]] = []

        for chunk_start, chunk_end in _monthly_chunks(start_date, end_date):
            filters = [
                {
                    "field": date_field,
                    "operator": "gte",
                    "value": _serialize_date_filter_value(
                        field_name=date_field,
                        field_type=date_field_type,
                        value=chunk_start,
                    ),
                },
                {
                    "field": date_field,
                    "operator": "lte",
                    "value": _serialize_date_filter_value(
                        field_name=date_field,
                        field_type=date_field_type,
                        value=chunk_end,
                    ),
                },
            ]
            if extra_filters:
                filters.extend(extra_filters)

            payload = self.query_table(table_name, filters=filters)
            chunk_rows = payload.get("rows", [])
            rows.extend(chunk_rows)

        return rows


def _first_day_of_next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _monthly_chunks(start_date: date, end_date: date) -> list[tuple[date, date]]:
    if start_date > end_date:
        return []

    chunks: list[tuple[date, date]] = []
    current_start = start_date

    while current_start <= end_date:
        next_month_start = _first_day_of_next_month(current_start)
        current_end = min(end_date, next_month_start - timedelta(days=1))
        chunks.append((current_start, current_end))
        current_start = next_month_start

    return chunks


def _serialize_date_filter_value(
    *, field_name: str, field_type: str, value: date
) -> Any:
    normalized_type = (field_type or "").upper()
    normalized_name = field_name.lower()

    if normalized_type in {"DATE", "DATETIME", "TIMESTAMP", "STRING"}:
        return value.isoformat()

    if normalized_type in {"INTEGER", "INT64", "NUMERIC", "BIGNUMERIC"}:
        # Some tables encode months as YYYYMM in integer columns.
        if "mois" in normalized_name or "month" in normalized_name:
            return int(value.strftime("%Y%m"))
        # Default numeric date serialization is YYYYMMDD.
        return int(value.strftime("%Y%m%d"))

    return value.isoformat()
