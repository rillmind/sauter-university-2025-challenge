# provider "google" {
  # project = "project-sauter-hydro-forecast"
  # region  = "us-central1"
# }

resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "run.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com"
  ])

  project = "project-sauter-hydro-forecast"
  service = each.value
}

# Bucket para dados
resource "google_storage_bucket" "ena_data" {
  name     = "ena-data-project-sauter-hydro-forecast"
  location = "us-central1"

  depends_on = [google_project_service.apis]
}

# Dataset BigQuery
resource "google_bigquery_dataset" "ena_dataset" {
  dataset_id    = "ena_analytics"
  friendly_name = "ENA Analytics Dataset"
  location      = "us-central1"

  depends_on = [google_project_service.apis]
}

# Service Account para GitHub
resource "google_service_account" "github_actions_sa" {
  account_id   = "github-actions-sa"
  display_name = "GitHub Actions Service Account"

  depends_on = [google_project_service.apis]
}

# Permissões para GitHub SA
resource "google_project_iam_member" "github_sa_permissions" {
  for_each = toset([
    "roles/run.admin",
    "roles/storage.admin",
    "roles/bigquery.admin",
    "roles/iam.serviceAccountUser"
  ])

  project = "project-sauter-hydro-forecast"
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Pool"

  depends_on = [google_project_service.apis]
}

# GitHub Workload Identity Provider (corrigido)
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id           = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id  = "github-provider"
  display_name                       = "GitHub Provider"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"        = "assertion.sub"
    "attribute.actor"       = "assertion.actor"
    "attribute.aud"         = "assertion.aud"
    "attribute.repository"  = "assertion.repository"
    "attribute.workflow"    = "assertion.workflow"
    "attribute.ref"         = "assertion.ref"
    "attribute.sha"         = "assertion.sha"
    "attribute.event_name"  = "assertion.event_name"
  }

  attribute_condition = "attribute.repository == 'danieladosanjos/project-sauter-hydro-forecast'"
}

# Permitir GitHub usar a Service Account via Workload Identity Federation
resource "google_service_account_iam_member" "github_wif" {
  service_account_id = google_service_account.github_actions_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/danieladosanjos/project-sauter-hydro-forecast"
}
