from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_CORS_ORIGINS = (
    "http://localhost:8501",
    "http://127.0.0.1:8501",
)


def load_environment() -> None:
    repo_root_env = Path(__file__).resolve().parents[3] / ".env"
    if repo_root_env.exists():
        load_dotenv(repo_root_env, override=False)
    load_dotenv(override=False)


@dataclass(frozen=True)
class Settings:
    project_id: str
    dataset_id: str
    credentials_path: Path
    default_limit: int = 100
    max_limit: int = 1000
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: DEFAULT_CORS_ORIGINS
    )
    include_hidden_tables: bool = False


def _parse_origins(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return DEFAULT_CORS_ORIGINS
    origins = tuple(origin.strip() for origin in raw_value.split(",") if origin.strip())
    return origins or DEFAULT_CORS_ORIGINS


def load_settings() -> Settings:
    load_environment()

    project_id = os.getenv("PROJECT_ID")
    dataset_id_base = os.getenv("DATASET_ID_PROD") or os.getenv("DATASET_ID_DEV")
    dataset_id = f"{dataset_id_base}_gold" if dataset_id_base else None
    credentials_value = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_value:
        credentials_value = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_CONTAINER")

    if not project_id:
        raise ValueError("PROJECT_ID is missing from the environment")
    if not dataset_id:
        raise ValueError(
            "DATASET_ID_PROD or DATASET_ID_DEV is missing from the environment"
        )
    if not credentials_value:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS is missing from the environment"
        )

    default_limit = int(os.getenv("FASTAPI_DEFAULT_LIMIT", "100"))
    max_limit = int(os.getenv("FASTAPI_MAX_LIMIT", "1000"))
    origins = _parse_origins(os.getenv("FASTAPI_CORS_ORIGINS"))

    return Settings(
        project_id=project_id,
        dataset_id=dataset_id,
        credentials_path=Path(credentials_value).expanduser(),
        default_limit=default_limit,
        max_limit=max_limit,
        allowed_origins=origins,
    )
