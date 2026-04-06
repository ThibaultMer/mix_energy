FROM apache/airflow:3.1.8

WORKDIR /opt/project

# Use numeric UID:GID to avoid buildkit host mapping issues
# airflow user in apache/airflow:3.1.8 typically has UID 50000, GID 0
COPY --chown=50000:0 pyproject.toml poetry.lock README.md ./
COPY --chown=50000:0 src ./src

USER airflow

RUN pip install --no-cache-dir .
