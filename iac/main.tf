# Dataset BigQuery gold
resource "google_bigquery_dataset" "gold_dataset_mix_energie" {
  dataset_id     = "gold_mix_energie"
  location       = var.location
  friendly_name  = "Dataset gold mix-energie"
  description    = "Dataset gold pour le projet mix-energie."
  project        = var.project_id
  delete_contents_on_destroy = true
}
# Dataset BigQuery silver
resource "google_bigquery_dataset" "silver_dataset_mix_energie" {
  dataset_id     = "silver_mix_energie"
  location       = var.location
  friendly_name  = "Dataset silver mix-energie"
  description    = "Dataset silver pour le projet mix-energie."
  project        = var.project_id
  delete_contents_on_destroy = true
}
# Activation de l'API Vertex AI
resource "google_project_service" "vertex_ai" {
  project = google_project.mix_energie_gcp.project_id
  service = "aiplatform.googleapis.com"
}
# Attribution du rôle Storage Object Admin au service account FastAPI
resource "google_storage_bucket_iam_member" "fastapi_mix_energie_object_admin" {
  bucket = google_storage_bucket.mix_energie_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.fastapi_mix_energie.email}"
}
# Message d'instructions pour l'utilisateur
output "instructions_service_account_admin" {
  value = <<EOT
⚠️ La première exécution de 'terraform apply' peut échouer avec une erreur de permission lors de la création des comptes de service.
Ce comportement est normal : le rôle 'Service Account Admin' vient d'être attribué à votre utilisateur.
Relancez simplement 'terraform apply -auto-approve -var-file="auto.tfvars"' une seconde fois pour poursuivre le déploiement.
EOT
}
# Attribution automatique du rôle Service Account Admin à l'utilisateur principal
resource "google_project_iam_member" "self_service_account_admin" {
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/iam.serviceAccountAdmin"
  member  = "user:${var.gcp_user_email}"
}
# Création automatique du projet GCP et activation des APIs
resource "google_project" "mix_energie_gcp" {
  name            = "mix-energie-gcp2"
  project_id      = "mix-energie-gcp2-492212"
  org_id          = "1064330306973" # Remplacez par votre org_id numérique si besoin
  billing_account = "01FE1B-B3B34E-92A1B4" # Remplacez par votre compte de facturation
  auto_create_network = true
}

resource "google_project_service" "compute" {
  project = google_project.mix_energie_gcp.project_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "bigquery" {
  project = google_project.mix_energie_gcp.project_id
  service = "bigquery.googleapis.com"
}

resource "google_project_service" "storage" {
  project = google_project.mix_energie_gcp.project_id
  service = "storage.googleapis.com"
}
# Dataset BigQuery principal
resource "google_bigquery_dataset" "mix_energie_dataset" {
  dataset_id     = "bronze_mix_energie"
  location       = var.location
  friendly_name  = "Dataset principal mix-energie"
  description    = "Dataset principal pour le projet mix-energie."
  project        = var.project_id
  delete_contents_on_destroy = true
}
# Droit d'écriture BigQuery pour import-mix-energie
resource "google_project_iam_member" "import_mix_energie_bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.import_mix_energie.email}"
}
# Service account pour l'import avec droit écriture sur le bucket
resource "google_service_account" "import_mix_energie" {
  account_id   = "import-mix-energie"
  description  = "Service account pour l'import, avec droit écriture sur le bucket mix-energie-bucket."
}

resource "google_storage_bucket_iam_member" "import_mix_energie_writer" {
  bucket = google_storage_bucket.mix_energie_bucket.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.import_mix_energie.email}"
}
# Service account pour FastAPI
resource "google_service_account" "fastapi_mix_energie" {
  account_id   = "fastapi-mix-energie"
  description  = "Service account dédié à l'application FastAPI mix-energie."
}
# Service account pour le bucket GCS
resource "google_service_account" "bucket_mix_energie" {
  account_id   = "bucket-mix-energie"
  description  = "Service account dédié au bucket mix-energie-bucket."
}

# Attribution du rôle Storage Admin au service account sur le bucket
resource "google_storage_bucket_iam_member" "bucket_mix_energie_admin" {
  bucket = google_storage_bucket.mix_energie_bucket.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.bucket_mix_energie.email}"
}
# Bucket GCS pour stockage des données
resource "google_storage_bucket" "mix_energie_bucket" {
  name     = "mix-energie-bucket-492212"
  location = var.location
  project  = var.project_id
  force_destroy = true
  uniform_bucket_level_access = true
}
resource "google_compute_instance" "vm_mix_energie" {
  name         = "vm-mix-energie"
  machine_type = var.vm_machine_type
  zone         = var.vm_zone
  project      = google_project.mix_energie_gcp.project_id

  boot_disk {
    initialize_params {
      image = var.vm_image_family
    }
  }

  network_interface {
    network = "default"
    access_config {
    }
  }

  tags = ["demo"]
}
resource "google_service_account" "mix_energie_bigquery" {
  account_id  = "bigquery-mix-energie"
  description = "Service account pour BigQuery avec droits BigQuery Admin."
}

resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id                  = "demo_dataset_${terraform.workspace}"
  location                    = var.location
  friendly_name               = "Demo Dataset ${terraform.workspace}"
  description                 = "Dataset jetable pour démo Terraform."
  delete_contents_on_destroy  = true
}

resource "google_project_iam_member" "mix_energie_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.mix_energie_bigquery.email}"
}


# Optionnel : exemple de table jetable
resource "google_bigquery_table" "demo_table" {
  dataset_id = google_bigquery_dataset.demo_dataset.dataset_id
  table_id   = "demo_table_${terraform.workspace}"
  schema     = <<EOF
[
  {"name": "id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "value", "type": "INTEGER", "mode": "NULLABLE"}
]
EOF
}
