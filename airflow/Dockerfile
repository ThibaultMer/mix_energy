FROM apache/airflow:3.1.8

WORKDIR /opt/project

COPY predict/dist/*.whl /opt/project

# Use numeric UID:GID to avoid buildkit host mapping issues
# airflow user in apache/airflow:3.1.8 typically has UID 50000, GID 0
COPY --chown=50000:0 ingest_dbt/pyproject.toml ingest_dbt/poetry.lock README.md ./
COPY --chown=50000:0 ingest_dbt/src ./src
COPY --chown=50000:0 dbt ./dbt

RUN mkdir -p /home/airflow/.dbt && chown airflow: /home/airflow/.dbt

USER airflow

RUN pip --no-cache-dir install *.whl

COPY dbt/profiles.yml.exemple /home/airflow/.dbt/profiles.yml

RUN pip install --no-cache-dir .
RUN pip install dbt-core
RUN pip install dbt-bigquery
