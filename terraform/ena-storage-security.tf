# terraform/ena-storage-security.tf
# Patch: Buckets Bronze/Silver/Gold + Logging/Versioning + Secret Manager

locals {
  project_id = "project-sauter-hydro-forecast"
  region     = "us-central1"
  suffix     = "sauter-hydro-forecast"
}

# Bucket para logs centralizados
resource "google_storage_bucket" "ena_logs" {
  name     = "ena-data-logs-${local.suffix}"
  location = "US-CENTRAL1"

  versioning {
    enabled = true
  }

  retention_policy {
    retention_period = 315360000 # 10 anos
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 3650
    }
  }

  depends_on = [google_project_service.apis]
}

# Bucket Bronze
resource "google_storage_bucket" "ena_bronze" {
  name     = "ena-data-bronze-${local.suffix}"
  location = "US-CENTRAL1"

  versioning {
    enabled = true
  }

  logging {
    log_bucket        = google_storage_bucket.ena_logs.name
    log_object_prefix = "bronze-logs/"
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90
    }
  }

  depends_on = [google_project_service.apis]
}

# Bucket Silver
resource "google_storage_bucket" "ena_silver" {
  name     = "ena-data-silver-${local.suffix}"
  location = "US-CENTRAL1"

  versioning {
    enabled = true
  }

  logging {
    log_bucket        = google_storage_bucket.ena_logs.name
    log_object_prefix = "silver-logs/"
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365
    }
  }

  depends_on = [google_project_service.apis]
}

# Bucket Gold
resource "google_storage_bucket" "ena_gold" {
  name     = "ena-data-gold-${local.suffix}"
  location = "US-CENTRAL1"

  versioning {
    enabled = true
  }

  logging {
    log_bucket        = google_storage_bucket.ena_logs.name
    log_object_prefix = "gold-logs/"
  }

  # sem lifecycle (dados permanentes)
  depends_on = [google_project_service.apis]
}

# IAM: permitir escrita nos buckets pela SA do pipeline
resource "google_storage_bucket_iam_member" "ena_bronze_writer" {
  bucket = google_storage_bucket.ena_bronze.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.sa_ena_pipeline.email}"
}

resource "google_storage_bucket_iam_member" "ena_silver_writer" {
  bucket = google_storage_bucket.ena_silver.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.sa_ena_pipeline.email}"
}

resource "google_storage_bucket_iam_member" "ena_gold_writer" {
  bucket = google_storage_bucket.ena_gold.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.sa_ena_pipeline.email}"
}

# IAM: permitir GitHub Actions SA administrar os buckets (opcional)
resource "google_storage_bucket_iam_member" "ena_bronze_github" {
  bucket = google_storage_bucket.ena_bronze.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

resource "google_storage_bucket_iam_member" "ena_silver_github" {
  bucket = google_storage_bucket.ena_silver.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

resource "google_storage_bucket_iam_member" "ena_gold_github" {
  bucket = google_storage_bucket.ena_gold.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

resource "google_secret_manager_secret" "sa_ena_key" {
  secret_id = "sa-ena-pipeline-key"

  replication {
    auto {}
  }

    rotation {
    rotation_period = "2160h" # 90 dias
  }

  depends_on = [google_project_service.apis]
}

# Acesso ao Secret para SA do pipeline
resource "google_secret_manager_secret_iam_member" "sa_ena_secret_accessor" {
  secret_id = google_secret_manager_secret.sa_ena_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sa_ena_pipeline.email}"
}

# (Opcional) GitHub Actions também pode acessar o Secret
resource "google_secret_manager_secret_iam_member" "github_secret_accessor" {
  secret_id = google_secret_manager_secret.sa_ena_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Outputs úteis
output "ena_bronze_bucket" {
  description = "GCS Bronze bucket"
  value       = google_storage_bucket.ena_bronze.url
}

output "ena_silver_bucket" {
  description = "GCS Silver bucket"
  value       = google_storage_bucket.ena_silver.url
}

output "ena_gold_bucket" {
  description = "GCS Gold bucket"
  value       = google_storage_bucket.ena_gold.url
}

output "ena_logs_bucket" {
  description = "GCS Logs bucket"
  value       = google_storage_bucket.ena_logs.url
}

output "sa_ena_secret_id" {
  description = "Secret Manager id for SA key"
  value       = google_secret_manager_secret.sa_ena_key.secret_id
}
