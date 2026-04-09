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

# .PHONY: build_gcp
# build_gcp:
# # Build the image for GCP (Linux/amd64 platform required for Cloud Run)
# 	docker build --platform linux/amd64 -t ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE} --file fastapi/Dockerfile .

.PHONY: run_local
run_local:
# Run local image
	@echo "Run the docker image"
	docker run --rm -p 8888:8888 \
			--volume ${PWD}/data:/app/data:ro \
			-e PROJECT_ID=${PROJECT_ID} \
			-e DATASET_ID_PROD=${DATASET_ID_PROD} \
			-e GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS} \
			-e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
			${IMAGE}

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
