#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"

echo "[1/3] Reinitialisation de l'etat Terraform local..."
rm -f terraform.tfstate terraform.tfstate.backup
rm -rf .terraform

echo "[2/3] Reinitialisation Terraform..."
terraform init

echo "[3/3] Bootstrap du projet puis import du bucket existant..."
terraform apply -auto-approve -var-file="auto.tfvars"
terraform import -var-file="auto.tfvars" -var='bootstrap_only=false' 'google_storage_bucket.mix_energie_bucket[0]' mix-energie-bucket

echo "Bucket importe. Vous pouvez maintenant lancer :"
echo "terraform apply -auto-approve -var-file=auto.tfvars -var='bootstrap_only=false'"