resource "google_compute_instance" "default" {
  name         = var.vm_name
  machine_type = var.vm_machine_type
  zone         = var.vm_zone

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
resource "google_service_account" "bq_demo" {
  account_id  = "bq-demo-sa-${terraform.workspace}"
  description = "Service account pour BigQuery demo, jetable et réutilisable."
}

resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id                  = "demo_dataset_${terraform.workspace}"
  location                    = var.location
  friendly_name               = "Demo Dataset ${terraform.workspace}"
  description                 = "Dataset jetable pour démo Terraform."
  delete_contents_on_destroy  = true
}

resource "google_project_iam_member" "bq_sa_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.bq_demo.email}"
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
