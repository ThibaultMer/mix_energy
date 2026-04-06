Airflow install

Prerequisites
- Docker and Docker Compose installed.
- Copy the shared environment template:
	cp .env.copy .env

Configure your local user IDs in .env (Linux)
- AIRFLOW_UID must match your host user ID.
- Commands to get them:
	id -u

Start Airflow
- Build/start initialization:
	docker compose -f airflow/docker-compose.yaml up airflow-init
- Start the full stack:
	docker compose -f airflow/docker-compose.yaml up -d --build

Notes
- This UID setup prevents permission issues on mounted folders (airflow/dags, airflow/logs, airflow/config, airflow/plugins).
- Airflow API/UI is exposed on localhost:8081.
