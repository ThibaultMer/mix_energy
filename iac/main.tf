locals {
  project_bucket_name = var.project_bucket_name
  bucket_location     = "EU"
}

resource "google_project" "mix_energie_gcp" {
  name                = var.project_name
  project_id          = var.project_id
  org_id              = var.org_id
  billing_account     = var.billing_account
  auto_create_network = true
}

resource "google_project_service" "compute" {
  project            = google_project.mix_energie_gcp.project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false

  depends_on = [google_project.mix_energie_gcp]
}

resource "google_project_service" "bigquery" {
  project            = google_project.mix_energie_gcp.project_id
  service            = "bigquery.googleapis.com"
  disable_on_destroy = false

  depends_on = [google_project.mix_energie_gcp]
}

resource "google_project_service" "storage" {
  project            = google_project.mix_energie_gcp.project_id
  service            = "storage.googleapis.com"
  disable_on_destroy = false

  depends_on = [google_project.mix_energie_gcp]
}

resource "google_project_service" "vertex_ai" {
  project            = google_project.mix_energie_gcp.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false

  depends_on = [google_project.mix_energie_gcp]
}

resource "google_project_service" "artifact_registry" {
  project            = google_project.mix_energie_gcp.project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false

  depends_on = [google_project.mix_energie_gcp]
}

resource "google_project_iam_member" "self_service_account_admin" {
  count   = var.bootstrap_only ? 0 : 1
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/iam.serviceAccountAdmin"
  member  = "user:${var.gcp_user_email}"

  depends_on = [
    google_project.mix_energie_gcp,
    google_project_service.compute,
    google_project_service.bigquery,
    google_project_service.storage,
    google_project_service.vertex_ai,
    google_project_service.artifact_registry,
  ]
}

resource "google_service_account" "import_mix_energie" {
  count        = var.bootstrap_only ? 0 : 1
  project      = google_project.mix_energie_gcp.project_id
  account_id   = "import-mix-energie"
  description  = "Service account pour l'import, avec droit ecriture sur le bucket mix-energie-bucket."

  depends_on = [google_project_iam_member.self_service_account_admin]
}

resource "google_service_account" "fastapi_mix_energie" {
  count        = var.bootstrap_only ? 0 : 1
  project      = google_project.mix_energie_gcp.project_id
  account_id   = "fastapi-mix-energie"
  description  = "Service account dedie a l'application FastAPI mix-energie."

  depends_on = [google_project_iam_member.self_service_account_admin]
}

resource "google_service_account" "bucket_mix_energie" {
  count        = var.bootstrap_only ? 0 : 1
  project      = google_project.mix_energie_gcp.project_id
  account_id   = "bucket-mix-energie"
  description  = "Service account dedie au bucket mix-energie-bucket."

  depends_on = [google_project_iam_member.self_service_account_admin]
}

resource "google_service_account" "mix_energie_bigquery" {
  count       = var.bootstrap_only ? 0 : 1
  project     = google_project.mix_energie_gcp.project_id
  account_id  = "bigquery-mix-energie"
  description = "Service account pour BigQuery avec droits BigQuery Admin."

  depends_on = [google_project_iam_member.self_service_account_admin]
}

resource "google_service_account" "airflow_mix_energie" {
  count                        = var.bootstrap_only ? 0 : 1
  project                      = google_project.mix_energie_gcp.project_id
  account_id                   = "airflow-mix-energie"
  description                  = "Service account dedie a Airflow pour consommer les artefacts du projet."

  depends_on = [google_project_iam_member.self_service_account_admin]
}

resource "google_service_account" "vm_mix_energie" {
  count                        = var.bootstrap_only ? 0 : 1
  project                      = google_project.mix_energie_gcp.project_id
  account_id                   = "vm-mix-energie"
  description                  = "Service account dedie a la VM pour lire Artifact Registry."

  depends_on = [google_project_iam_member.self_service_account_admin]
}

resource "google_artifact_registry_repository" "docker" {
  count         = var.bootstrap_only ? 0 : 1
  location      = var.artifact_registry_location
  project       = google_project.mix_energie_gcp.project_id
  repository_id = "mix-energie-docker"
  description   = "Depot Artifact Registry pour les images Docker du projet."
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

resource "google_artifact_registry_repository_iam_member" "airflow_docker_reader" {
  count      = var.bootstrap_only ? 0 : 1
  project    = google_project.mix_energie_gcp.project_id
  location   = google_artifact_registry_repository.docker[0].location
  repository = google_artifact_registry_repository.docker[0].name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.airflow_mix_energie[0].email}"

  depends_on = [
    google_service_account.airflow_mix_energie,
    google_artifact_registry_repository.docker,
  ]
}

resource "google_artifact_registry_repository_iam_member" "airflow_docker_writer" {
  count      = var.bootstrap_only ? 0 : 1
  project    = google_project.mix_energie_gcp.project_id
  location   = google_artifact_registry_repository.docker[0].location
  repository = google_artifact_registry_repository.docker[0].name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.airflow_mix_energie[0].email}"

  depends_on = [
    google_service_account.airflow_mix_energie,
    google_artifact_registry_repository.docker,
  ]
}

resource "google_artifact_registry_repository_iam_member" "airflow_standard_reader" {
  count      = var.bootstrap_only ? 0 : 1
  project    = google_project.mix_energie_gcp.project_id
  location   = google_artifact_registry_repository.standard[0].location
  repository = google_artifact_registry_repository.standard[0].name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.airflow_mix_energie[0].email}"

  depends_on = [
    google_service_account.airflow_mix_energie,
    google_artifact_registry_repository.standard,
  ]
}

resource "google_artifact_registry_repository_iam_member" "airflow_standard_writer" {
  count      = var.bootstrap_only ? 0 : 1
  project    = google_project.mix_energie_gcp.project_id
  location   = google_artifact_registry_repository.standard[0].location
  repository = google_artifact_registry_repository.standard[0].name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.airflow_mix_energie[0].email}"

  depends_on = [
    google_service_account.airflow_mix_energie,
    google_artifact_registry_repository.standard,
  ]
}

resource "google_storage_bucket" "mix_energie_bucket" {
  count                       = var.bootstrap_only ? 0 : 1
  name                        = local.project_bucket_name
  location                    = local.bucket_location
  project                     = google_project.mix_energie_gcp.project_id
  uniform_bucket_level_access = true

  depends_on = [google_project_service.storage]
}

resource "google_storage_bucket_iam_member" "fastapi_mix_energie_object_admin" {
  count  = var.bootstrap_only ? 0 : 1
  bucket = google_storage_bucket.mix_energie_bucket[0].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.fastapi_mix_energie[0].email}"

  depends_on = [
    google_storage_bucket.mix_energie_bucket,
    google_service_account.fastapi_mix_energie,
  ]
}

resource "google_storage_bucket_iam_member" "import_mix_energie_writer" {
  count  = var.bootstrap_only ? 0 : 1
  bucket = google_storage_bucket.mix_energie_bucket[0].name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.import_mix_energie[0].email}"

  depends_on = [
    google_storage_bucket.mix_energie_bucket,
    google_service_account.import_mix_energie,
  ]
}

resource "google_storage_bucket_iam_member" "bucket_mix_energie_admin" {
  count  = var.bootstrap_only ? 0 : 1
  bucket = google_storage_bucket.mix_energie_bucket[0].name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.bucket_mix_energie[0].email}"

  depends_on = [
    google_storage_bucket.mix_energie_bucket,
    google_service_account.bucket_mix_energie,
  ]
}

resource "google_project_iam_member" "import_mix_energie_bigquery_editor" {
  count   = var.bootstrap_only ? 0 : 1
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.import_mix_energie[0].email}"

  depends_on = [
    google_project_service.bigquery,
    google_service_account.import_mix_energie,
  ]
}

resource "google_project_iam_member" "mix_energie_bigquery_admin" {
  count   = var.bootstrap_only ? 0 : 1
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.mix_energie_bigquery[0].email}"

  depends_on = [
    google_project_service.bigquery,
    google_service_account.mix_energie_bigquery,
  ]
}

resource "google_project_iam_member" "airflow_bigquery_data_editor" {
  count   = var.bootstrap_only ? 0 : 1
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.airflow_mix_energie[0].email}"

  depends_on = [
    google_project_service.bigquery,
    google_service_account.airflow_mix_energie,
  ]
}

resource "google_project_iam_member" "airflow_bigquery_job_user" {
  count   = var.bootstrap_only ? 0 : 1
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.airflow_mix_energie[0].email}"

  depends_on = [
    google_project_service.bigquery,
    google_service_account.airflow_mix_energie,
  ]
}

resource "google_project_iam_member" "airflow_storage_object_admin" {
  count   = var.bootstrap_only ? 0 : 1
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.airflow_mix_energie[0].email}"

  depends_on = [
    google_project_service.storage,
    google_service_account.airflow_mix_energie,
  ]
}

resource "google_project_iam_member" "airflow_storage_object_viewer" {
  count   = var.bootstrap_only ? 0 : 1
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.airflow_mix_energie[0].email}"

  depends_on = [
    google_project_service.storage,
    google_service_account.airflow_mix_energie,
  ]
}

resource "google_project_iam_member" "vm_artifact_registry_reader" {
  count   = var.bootstrap_only ? 0 : 1
  project = google_project.mix_energie_gcp.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.vm_mix_energie[0].email}"

  depends_on = [
    google_project_service.artifact_registry,
    google_service_account.vm_mix_energie,
  ]
}

resource "google_bigquery_dataset" "dev_mix_energie_dataset" {
  count                      = var.bootstrap_only ? 0 : 1
  dataset_id                 = "dev_mix_energie"
  location                   = var.location
  friendly_name              = "dev-mix-energie"
  description                = "Dataset de dev bronze pour le projet mix-energie."
  project                    = google_project.mix_energie_gcp.project_id

  depends_on = [google_project_service.bigquery]
}

resource "google_bigquery_dataset" "prod_mix_energie_dataset" {
  count                      = var.bootstrap_only ? 0 : 1
  dataset_id                 = "prod_mix_energie"
  location                   = var.location
  friendly_name              = "prod-mix-energie"
  description                = "Dataset de prod bronze pour le projet mix-energie."
  project                    = google_project.mix_energie_gcp.project_id

  depends_on = [google_project_service.bigquery]
}

resource "google_bigquery_dataset" "dev_mix_energie_silver_dataset" {
  count                      = var.bootstrap_only ? 0 : 1
  dataset_id                 = "dev_mix_energie_silver"
  location                   = var.location
  friendly_name              = "dev-mix-energie-silver"
  description                = "Dataset de dev silver pour le projet mix-energie."
  project                    = google_project.mix_energie_gcp.project_id

  depends_on = [google_project_service.bigquery]
}

resource "google_bigquery_dataset" "prod_mix_energie_silver_dataset" {
  count                      = var.bootstrap_only ? 0 : 1
  dataset_id                 = "prod_mix_energie_silver"
  location                   = var.location
  friendly_name              = "prod-mix-energie-silver"
  description                = "Dataset de prod silver pour le projet mix-energie."
  project                    = google_project.mix_energie_gcp.project_id

  depends_on = [google_project_service.bigquery]
}

resource "google_bigquery_dataset" "dev_mix_energie_gold_dataset" {
  count                      = var.bootstrap_only ? 0 : 1
  dataset_id                 = "dev_mix_energie_gold"
  location                   = var.location
  friendly_name              = "dev-mix-energie-gold"
  description                = "Dataset de dev gold pour le projet mix-energie."
  project                    = google_project.mix_energie_gcp.project_id

  depends_on = [google_project_service.bigquery]
}

resource "google_bigquery_dataset" "prod_mix_energie_gold_dataset" {
  count                      = var.bootstrap_only ? 0 : 1
  dataset_id                 = "prod_mix_energie_gold"
  location                   = var.location
  friendly_name              = "prod-mix-energie-gold"
  description                = "Dataset de prod gold pour le projet mix-energie."
  project                    = google_project.mix_energie_gcp.project_id

  depends_on = [google_project_service.bigquery]
}

resource "google_compute_instance" "vm_mix_energie" {
  count                     = var.bootstrap_only ? 0 : 1
  allow_stopping_for_update = true
  name                      = var.vm_name
  machine_type              = var.vm_machine_type
  zone                      = var.vm_zone
  project                   = google_project.mix_energie_gcp.project_id
  deletion_protection = false

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

  service_account {
    email  = google_service_account.vm_mix_energie[0].email
    scopes = ["cloud-platform"]
  }

  tags = ["demo"]

  depends_on = [
    google_project_service.compute,
    google_project_iam_member.vm_artifact_registry_reader,
  ]
}

output "instructions_service_account_admin" {
  value = var.bootstrap_only ? "Phase bootstrap terminee.\n\nEtape suivante:\n1. Verifiez que ${var.gcp_user_email} a le role Owner sur le projet ${var.project_id}.\n2. Relancez Terraform avec bootstrap_only=false pour creer les comptes de service, le bucket, les datasets et la VM." : "Deploiement complet termine.\nSi une erreur IAM apparait pendant la phase complete, verifiez que ${var.gcp_user_email} est bien Owner du projet ${var.project_id} puis relancez la commande."
}
