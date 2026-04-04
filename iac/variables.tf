variable "gcp_user_email" {
  type        = string
  description = "Adresse e-mail de l'utilisateur principal pour l'attribution IAM (ex: user@domaine.com)"
}
variable "org_id" {
  type        = string
  description = "ID de l'organisation GCP (ex: 123456789012)"
}

variable "billing_account" {
  type        = string
  description = "ID du compte de facturation GCP (ex: 01A1B2-123456-7890AB)"
}
variable "vm_name" {
  description = "Nom de l'instance VM"
  type        = string
  default     = "vm-mix-energie"
}

variable "vm_zone" {
  description = "Zone de déploiement de la VM"
  type        = string
  default     = "europe-west1-b"
}

variable "vm_machine_type" {
  description = "Type de machine de la VM"
  type        = string
  default     = "e2-micro"
}

variable "vm_image_family" {
  description = "Famille d'image pour le disque boot"
  type        = string
  default     = "debian-11"
}

variable "vm_image_project" {
  description = "Projet de l'image pour le disque boot"
  type        = string
  default     = "debian-cloud"
}
variable "location" {
  type        = string
  description = "Location where the GCP resources will be created for mix-energy"
  default     = "EU"
}

variable "project_id" {
  type        = string
  description = "GCP project id where the resources will be created into."
}
