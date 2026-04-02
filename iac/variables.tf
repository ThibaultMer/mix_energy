variable "vm_name" {
  description = "Nom de l'instance VM"
  type        = string
  default     = "demo-vm"
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
