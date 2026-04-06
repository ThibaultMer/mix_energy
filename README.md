Airflow install

#Récupérer le docker contenant airflow
docker pull apache/airflow:3.1.8
#le docker compose est déjà dans  le repo dans le dossier airflow
docker compose -f airflow/docker-compose.yaml up airflow-init
