

.PHONY: first_init
firts_init :
	pip install poetry
	pip install pre-commit
	pip install codespell
	pre-commit install

.PHONY: setup
setup :
	@echo "Install the module"
    poetry install

########################################################################################################################

# REST API

########################################################################################################################
.PHONY: start_fastapi
start_fastapi:
	fastapi run rest/api.py --reload --port 8888

.PHONY: start_fastapi_dev
start_fastapi_dev:
	fastapi dev rest/api.py --reload --port 8888

########################################################################################################################

# Docker commands

########################################################################################################################
.PHONY: build_local
build_local:
	@echo "Build the docker ${IMAGE}"
	docker build -t ${IMAGE} --file rest/Dockerfile .

.PHONY: build_gcp
build_gcp:
# Build the image for GCP (Linux/amd64 platform required for Cloud Run)
	docker build --platform linux/amd64 -t ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE} --file rest/Dockerfil
e .

.PHONY: run_local
run_local: build_local
# Run local image
	@echo "Run the docker image"
	docker run -p ${HOST_PORT}:${PORT} -e PORT=${PORT} ${IMAGE}

.PHONY: push_gcp
push_gcp: build_gcp
# Push the image to Artifact Registry
	docker push ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE}

.PHONY: auth_gcp
auth_gcp:
	gcloud auth login
	gcloud config set project ${PROJECT_ID}

.PHONY: deploy
deploy:
	gcloud run deploy ${IMAGE} --image ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE} --region ${LOCATION} --pl
atform managed --allow-unauthenticated
