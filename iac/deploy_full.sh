#!/bin/bash
# Script pour automatiser le déploiement Terraform avec gestion du projet GCP
# Usage : bash deploy_full.sh

set -euo pipefail

cd "$(dirname "$0")"

PROJECT_ID=$(awk -F '"' '/^project_id[[:space:]]*=/{print $2}' auto.tfvars)
GCP_USER_EMAIL=$(awk -F '"' '/^gcp_user_email[[:space:]]*=/{print $2}' auto.tfvars)

if [[ -z "$PROJECT_ID" || -z "$GCP_USER_EMAIL" ]]; then
	echo "Impossible de lire project_id ou gcp_user_email depuis auto.tfvars." >&2
	exit 1
fi

# 1. Création du projet GCP uniquement
terraform apply -auto-approve -var-file="auto.tfvars" -target=google_project.mix_energie_gcp

# 2. Pause pour vérification des droits IAM
cat <<EOT

⚠️ Vérifiez que votre compte utilisateur a bien le rôle Owner ou IAM Admin sur le projet ${PROJECT_ID}.
Si besoin, ajoutez-le via la console GCP ou la commande suivante :
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="user:${GCP_USER_EMAIL}" --role="roles/owner"

Appuyez sur Entrée pour continuer une fois les droits confirmés...
EOT
read

# 3. Appliquer le reste de l'infrastructure
terraform apply -auto-approve -var-file="auto.tfvars"
