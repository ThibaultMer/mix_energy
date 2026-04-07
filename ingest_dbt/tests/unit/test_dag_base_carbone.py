from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


class _FakeTask:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.downstream = []

    def __rshift__(self, other):
        self.downstream.append(other)
        return other


class _FakeDag:
    def __init__(self, dag_id: str, schedule, tags: list[str]):
        self.dag_id = dag_id
        self.schedule = schedule
        self.tags = tags
        self.task_ids: list[str] = []


def _install_airflow_stubs(monkeypatch):
    airflow_module = types.ModuleType("airflow")
    decorators_module = types.ModuleType("airflow.sdk")
    providers_module = types.ModuleType("airflow.providers")
    providers_google_module = types.ModuleType("airflow.providers.google")
    providers_google_cloud_module = types.ModuleType("airflow.providers.google.cloud")
    providers_google_cloud_hooks_module = types.ModuleType(
        "airflow.providers.google.cloud.hooks"
    )
    gcs_hook_module = types.ModuleType("airflow.providers.google.cloud.hooks.gcs")
    bq_hook_module = types.ModuleType("airflow.providers.google.cloud.hooks.bigquery")

    current_tasks: list[_FakeTask] = []

    def dag(
        *,
        dag_id: str,
        schedule,
        catchup: bool,
        tags: list[str],
        description: str,
        start_date,
    ):
        def decorator(func):
            def wrapper():
                current_tasks.clear()
                result = func()
                fake_dag = _FakeDag(dag_id=dag_id, schedule=schedule, tags=tags)
                fake_dag.task_ids = [task.task_id for task in current_tasks]
                return fake_dag if result is None else result

            return wrapper

        return decorator

    def task(*, task_id: str):
        def decorator(func):
            def wrapper(*args, **kwargs):
                fake_task = _FakeTask(task_id=task_id)
                current_tasks.append(fake_task)
                return fake_task

            return wrapper

        return decorator

    decorators_module.dag = dag
    decorators_module.task = task

    class _FakeGCSHook:
        def __init__(self, *args, **kwargs):
            pass

        def list(self, *args, **kwargs):
            return []

        def upload(self, *args, **kwargs):
            return None

        def get_conn(self):
            class _FakeClient:
                def bucket(self, *args, **kwargs):
                    return object()

            return _FakeClient()

    class _FakeBigQueryHook:
        def __init__(self, *args, **kwargs):
            pass

        def get_client(self, *args, **kwargs):
            return object()

    gcs_hook_module.GCSHook = _FakeGCSHook
    bq_hook_module.BigQueryHook = _FakeBigQueryHook

    monkeypatch.setitem(sys.modules, "airflow", airflow_module)
    monkeypatch.setitem(sys.modules, "airflow.sdk", decorators_module)
    monkeypatch.setitem(sys.modules, "airflow.providers", providers_module)
    monkeypatch.setitem(
        sys.modules, "airflow.providers.google", providers_google_module
    )
    monkeypatch.setitem(
        sys.modules, "airflow.providers.google.cloud", providers_google_cloud_module
    )
    monkeypatch.setitem(
        sys.modules,
        "airflow.providers.google.cloud.hooks",
        providers_google_cloud_hooks_module,
    )
    monkeypatch.setitem(
        sys.modules, "airflow.providers.google.cloud.hooks.gcs", gcs_hook_module
    )
    monkeypatch.setitem(
        sys.modules,
        "airflow.providers.google.cloud.hooks.bigquery",
        bq_hook_module,
    )


def test_dag_base_carbone_structure(monkeypatch):
    _install_airflow_stubs(monkeypatch)

    path = (
        Path(__file__).resolve().parents[2] / "airflow" / "dags" / "dag_base_carbone.py"
    )
    spec = importlib.util.spec_from_file_location("dag_base_carbone", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    dag = module.dag

    assert dag.dag_id == "dag_base_carbone"
    assert dag.schedule == "30 9 1 * 1-5"
    assert dag.tags == ["base-carbone", "ingestion"]
    assert dag.task_ids == [
        "check_bucket_connection",
        "ingest_csv_to_bucket",
        "transfer_csv_to_bigquery",
    ]
