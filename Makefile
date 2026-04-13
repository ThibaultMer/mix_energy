########################################################################################################################

# COMMANDS FOR SETUP DEV ENVIRONMENT

########################################################################################################################

.PHONY: first_init
firts_init :
	pip install poetry
	pip install pre-commit
	pip install codespell
	pre-commit install

.PHONY: setup
setup :
	@echo "Install the module";
	poetry install

########################################################################################################################

# REST API

########################################################################################################################
.PHONY: start_fastapi
start_fastapi:
	fastapi run fastapi/main.py --reload --port 8888

.PHONY: start_fastapi_dev
start_fastapi_dev:
	fastapi dev fastapi/main.py --reload --port 8888

########################################################################################################################

# Docker commands

########################################################################################################################


.PHONY: build_predict
build_predict:
	@echo "Build the predict module";
	cd ${PWD}/predict && poetry build && cd ..;

.PHONY: clean_predict
clean_predict:
	rm -rf ${PWD}/predict/dist

.PHONY: build_local_fastapi
build_local_fastapi: build_predict
	cp ${PWD}/predict/dist/predict-*-py3-none-any.whl fastapi/;
	@echo "Build the docker ${IMAGE}"
	cd ${PWD}/fastapi && docker build -t ${IMAGE} . ;
	cd .. && rm ${PWD}/fastapi/*.whl;

.PHONY: build_local_airflow
build_local_airflow: build_predict
	docker compose -f airflow/docker-compose.yaml build

.PHONY: build_local_streamlit
build_local_streamlit:
	cd ${PWD}/front-streamlit && docker build -t "mix-energie-streamlit" . && cd .. ;

.PHONY: start_mlflow_server
start_mlflow_server:
	mlflow server --host=0.0.0.0 --port=5000

.PHONY: run_local_fastapi
run_local_fastapi:
# Run local image
	@echo "Run the docker image"
	docker run --rm -p ${HOST_PORT}:${PORT} \
			--volume ${PWD}/data:/app/data:ro \
			-e PROJECT_ID=${PROJECT_ID} \
			-e DATASET_ID_PROD=${DATASET_ID_PROD} \
			-e GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS} \
			-e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
			${IMAGE}

.PHONY: run_local_airflow
run_local_airflow:
	docker compose -f airflow/docker-compose.yaml up -d

.PHONY: stop_local_airflow
stop_local_airflow:
	docker compose -f airflow/docker-compose.yaml down

.PHONY: run_local_streamlit
run_local_streamlit:
	docker run --rm -p 8501:8501 "mix-energie-streamlit"

.PHONY: make_coffee
coffee: build_local_streamlit, build_local_fastapi, build_local_airflow

# .PHONY: run_cat
# run_cat: run_local_fastapi,run_local_airflow,run_local_streamlit,start_mlflow_server


# .PHONY: build_gcp
# build_gcp:
# # Build the image for GCP (Linux/amd64 platform required for Cloud Run)
# 	docker build --platform linux/amd64 -t ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE} --file fastapi/Dockerfile .
#
# .PHONY: push_gcp
# push_gcp: build_gcp
# # Push the image to Artifact Registry
# 	docker push ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE}

# .PHONY: auth_gcp
# auth_gcp:
# 	gcloud auth login
# 	gcloud config set project ${PROJECT_ID}

# .PHONY: deploy
# deploy:
# 	gcloud run deploy ${IMAGE} --image ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE} --region ${LOCATION} --platform managed --allow-unauthenticated
