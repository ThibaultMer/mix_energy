terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.24.0"
    }
  }
  backend "local" {}
}

provider "google" {
  project = var.project_id
}
