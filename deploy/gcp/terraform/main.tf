# GCP Infrastructure for Axion
# Terraform configuration for Google Cloud Platform

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "axion-terraform-state"
    prefix = "terraform/state"
  }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-northeast1-a"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# VPC Network
resource "google_compute_network" "axion" {
  name                    = "axion-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "axion" {
  name          = "axion-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.axion.id

  private_ip_google_access = true
}

# Firewall rules
resource "google_compute_firewall" "allow_http" {
  name    = "axion-allow-http"
  network = google_compute_network.axion.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["axion-web"]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "axion-allow-ssh"
  network = google_compute_network.axion.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"] # IAP range
  target_tags   = ["axion-web"]
}

# Cloud SQL Instance (PostgreSQL)
resource "google_sql_database_instance" "axion" {
  name             = "axion-postgres-${var.environment}"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.axion.id
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    maintenance_window {
      day  = 7
      hour = 4
    }
  }

  deletion_protection = true

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "axion" {
  name     = "axion"
  instance = google_sql_database_instance.axion.name
}

resource "google_sql_user" "axion" {
  name     = "axion"
  instance = google_sql_database_instance.axion.name
  password = var.db_password
}

# Cloud Storage Buckets
resource "google_storage_bucket" "artifacts" {
  name          = "${var.project_id}-axion-artifacts"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket" "deploy" {
  name          = "${var.project_id}-axion-artifacts-deploy"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Service Account for VM
resource "google_service_account" "axion_vm" {
  account_id   = "axion-vm"
  display_name = "Axion VM Service Account"
}

resource "google_project_iam_member" "vm_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.axion_vm.email}"
}

resource "google_project_iam_member" "vm_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.axion_vm.email}"
}

resource "google_project_iam_member" "vm_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.axion_vm.email}"
}

# GCE Instance
resource "google_compute_instance" "axion" {
  name         = "axion-vm"
  machine_type = "e2-small"
  zone         = var.zone

  tags = ["axion-web"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 20
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.axion.id

    access_config {
      // Ephemeral public IP
    }
  }

  service_account {
    email  = google_service_account.axion_vm.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = file("${path.module}/../vm-setup.sh")

  metadata = {
    CLOUD_SQL_INSTANCE = google_sql_database_instance.axion.connection_name
  }

  labels = {
    environment = var.environment
    app         = "axion"
  }

  allow_stopping_for_update = true

  depends_on = [google_project_service.apis]
}

# Workload Identity for GitHub Actions
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "github_actions" {
  account_id   = "github-actions-deploy"
  display_name = "GitHub Actions Deploy Service Account"
}

resource "google_service_account_iam_binding" "github_actions_wi" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/YOUR_GITHUB_ORG/axion"
  ]
}

resource "google_project_iam_member" "github_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_compute" {
  project = var.project_id
  role    = "roles/compute.instanceAdmin.v1"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Outputs
output "vm_external_ip" {
  description = "External IP of the VM"
  value       = google_compute_instance.axion.network_interface[0].access_config[0].nat_ip
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name for Cloud SQL Proxy"
  value       = google_sql_database_instance.axion.connection_name
}

output "artifacts_bucket" {
  description = "GCS bucket for artifacts"
  value       = google_storage_bucket.artifacts.name
}

output "deploy_bucket" {
  description = "GCS bucket for deployment artifacts"
  value       = google_storage_bucket.deploy.name
}

output "workload_identity_provider" {
  description = "Workload Identity Provider for GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "github_service_account" {
  description = "Service Account email for GitHub Actions"
  value       = google_service_account.github_actions.email
}
