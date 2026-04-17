#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"

PROJECT_ID=$(awk -F '"' '/^project_id[[:space:]]*=/{print $2}' auto.tfvars)
GCP_USER_EMAIL=$(awk -F '"' '/^gcp_user_email[[:space:]]*=/{print $2}' auto.tfvars)
PROJECT_BUCKET_NAME=$(awk -F '"' '/^project_bucket_name[[:space:]]*=/{print $2}' auto.tfvars)
ARTIFACT_REGISTRY_LOCATION=$(awk -F '"' '/^artifact_registry_location[[:space:]]*=/{print $2}' auto.tfvars)
VM_NAME=$(awk -F '"' '/^vm_name[[:space:]]*=/{print $2}' auto.tfvars)
VM_ZONE=$(awk -F '"' '/^vm_zone[[:space:]]*=/{print $2}' auto.tfvars)
ARTIFACT_REGISTRY_LOCATION=${ARTIFACT_REGISTRY_LOCATION:-europe-west1}
VM_NAME=${VM_NAME:-vm-mix-energie}
VM_ZONE=${VM_ZONE:-europe-west1-b}

if [[ -z "$PROJECT_ID" || -z "$GCP_USER_EMAIL" || -z "$PROJECT_BUCKET_NAME" ]]; then
	echo "Impossible de lire project_id, project_bucket_name ou gcp_user_email depuis auto.tfvars." >&2
	exit 1
fi

state_has() {
	terraform state list 2>/dev/null | grep -Fqx "$1"
}

import_if_exists() {
	local address="$1"
	local import_id="$2"
	local check_command="$3"

	if state_has "$address"; then
		return 0
	fi

	if eval "$check_command" >/dev/null 2>&1; then
		echo "Import de $address"
		terraform import -var-file="auto.tfvars" "$address" "$import_id"
	fi
}

echo "Bootstrap Terraform pour $PROJECT_ID"
terraform apply -auto-approve -var-file="auto.tfvars" -var='bootstrap_only=true'

echo "Activation explicite des APIs principales pour $PROJECT_ID"
gcloud services enable \
	bigquery.googleapis.com \
	compute.googleapis.com \
	storage.googleapis.com \
	aiplatform.googleapis.com \
	artifactregistry.googleapis.com \
	--project="$PROJECT_ID"

echo "Attribution du rôle Owner à $GCP_USER_EMAIL sur $PROJECT_ID"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
	--member="user:$GCP_USER_EMAIL" \
	--role="roles/owner"

echo "Réconciliation de l'existant avant l'apply complet"
import_if_exists "google_project.mix_energie_gcp" "projects/$PROJECT_ID" "gcloud projects describe $PROJECT_ID"
import_if_exists "google_service_account.import_mix_energie[0]" "projects/$PROJECT_ID/serviceAccounts/import-mix-energie@$PROJECT_ID.iam.gserviceaccount.com" "gcloud iam service-accounts describe import-mix-energie@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID"
import_if_exists "google_service_account.fastapi_mix_energie[0]" "projects/$PROJECT_ID/serviceAccounts/fastapi-mix-energie@$PROJECT_ID.iam.gserviceaccount.com" "gcloud iam service-accounts describe fastapi-mix-energie@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID"
import_if_exists "google_service_account.bucket_mix_energie[0]" "projects/$PROJECT_ID/serviceAccounts/bucket-mix-energie@$PROJECT_ID.iam.gserviceaccount.com" "gcloud iam service-accounts describe bucket-mix-energie@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID"
import_if_exists "google_service_account.mix_energie_bigquery[0]" "projects/$PROJECT_ID/serviceAccounts/bigquery-mix-energie@$PROJECT_ID.iam.gserviceaccount.com" "gcloud iam service-accounts describe bigquery-mix-energie@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID"
import_if_exists "google_service_account.airflow_mix_energie[0]" "projects/$PROJECT_ID/serviceAccounts/airflow-mix-energie@$PROJECT_ID.iam.gserviceaccount.com" "gcloud iam service-accounts describe airflow-mix-energie@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID"
import_if_exists "google_service_account.vm_mix_energie[0]" "projects/$PROJECT_ID/serviceAccounts/vm-mix-energie@$PROJECT_ID.iam.gserviceaccount.com" "gcloud iam service-accounts describe vm-mix-energie@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID"
import_if_exists "google_artifact_registry_repository.docker[0]" "projects/$PROJECT_ID/locations/$ARTIFACT_REGISTRY_LOCATION/repositories/mix-energie-docker" "gcloud artifacts repositories describe mix-energie-docker --location=$ARTIFACT_REGISTRY_LOCATION --project=$PROJECT_ID"
import_if_exists "google_artifact_registry_repository.standard[0]" "projects/$PROJECT_ID/locations/$ARTIFACT_REGISTRY_LOCATION/repositories/mix-energie-python" "gcloud artifacts repositories describe mix-energie-python --location=$ARTIFACT_REGISTRY_LOCATION --project=$PROJECT_ID"
import_if_exists "google_storage_bucket.mix_energie_bucket[0]" "$PROJECT_BUCKET_NAME" "gcloud storage buckets describe gs://$PROJECT_BUCKET_NAME"
import_if_exists "google_bigquery_dataset.mix_energie_dataset[0]" "projects/$PROJECT_ID/datasets/mix_energie_bronze" "bq --project_id=$PROJECT_ID show $PROJECT_ID:mix_energie_bronze"
import_if_exists "google_bigquery_dataset.silver_dataset_mix_energie[0]" "projects/$PROJECT_ID/datasets/mix_energie_silver" "bq --project_id=$PROJECT_ID show $PROJECT_ID:mix_energie_silver"
import_if_exists "google_bigquery_dataset.gold_dataset_mix_energie[0]" "projects/$PROJECT_ID/datasets/mix_energie_gold" "bq --project_id=$PROJECT_ID show $PROJECT_ID:mix_energie_gold"
import_if_exists "google_bigquery_dataset.demo_dataset[0]" "projects/$PROJECT_ID/datasets/demo_dataset_default" "bq --project_id=$PROJECT_ID show $PROJECT_ID:demo_dataset_default"
import_if_exists "google_bigquery_table.demo_table[0]" "$PROJECT_ID:demo_dataset_default.demo_table_default" "bq --project_id=$PROJECT_ID show $PROJECT_ID:demo_dataset_default.demo_table_default"
import_if_exists "google_compute_instance.vm_mix_energie[0]" "projects/$PROJECT_ID/zones/$VM_ZONE/instances/$VM_NAME" "gcloud compute instances describe $VM_NAME --zone=$VM_ZONE --project=$PROJECT_ID"

echo "Déploiement complet Terraform pour $PROJECT_ID"
terraform apply -auto-approve -var-file="auto.tfvars" -var='bootstrap_only=false'

echo "Datasets attendus: mix_energie_bronze, mix_energie_silver, mix_energie_gold"
