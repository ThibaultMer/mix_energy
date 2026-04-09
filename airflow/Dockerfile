FROM apache/airflow:3.1.8

WORKDIR /opt/project

COPY predict/dist/*.whl /opt/project

# Use numeric UID:GID to avoid buildkit host mapping issues
# airflow user in apache/airflow:3.1.8 typically has UID 50000, GID 0
COPY --chown=50000:0 ingest_dbt/pyproject.toml ingest_dbt/poetry.lock README.md ./
COPY --chown=50000:0 ingest_dbt/src ./src

USER airflow

RUN pip --no-cache-dir install *.whl

RUN pip install --no-cache-dir .
