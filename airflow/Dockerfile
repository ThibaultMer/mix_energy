FROM apache/airflow:3.1.8

WORKDIR /opt/project

COPY --chown=airflow:airflow pyproject.toml poetry.lock README.md ./
COPY --chown=airflow:airflow src ./src

USER airflow

RUN pip install --no-cache-dir .
