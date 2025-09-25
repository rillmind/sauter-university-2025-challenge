# terraform/ena-resources.tf 

# Tabela ENA no dataset existente
resource "google_bigquery_table" "ena_consolidado" {
  dataset_id = google_bigquery_dataset.ena_dataset.dataset_id
  table_id   = "ena_consolidado"

  time_partitioning {
    type  = "DAY"
    field = "ear_data"
  }

  clustering = ["cod_resplanejamento", "nom_subsistema"]

  schema = jsonencode([
    { "name" : "ear_data", "type" : "DATE", "mode" : "REQUIRED" },
    { "name" : "cod_resplanejamento", "type" : "INT64", "mode" : "REQUIRED" },
    { "name" : "nom_reservatorio", "type" : "STRING", "mode" : "REQUIRED" },
    { "name" : "ear_total_mwmes", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "ear_maxima_total_mwmes", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "ear_reservatorio_percentual", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "val_contribearbacia", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "val_contribearsin", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "nom_bacia", "type" : "STRING", "mode" : "REQUIRED" },
    { "name" : "nom_subsistema", "type" : "STRING", "mode" : "REQUIRED" },
    { "name" : "nom_ree", "type" : "STRING", "mode" : "NULLABLE" },
    { "name" : "tip_reservatorio", "type" : "STRING", "mode" : "REQUIRED" },
    { "name" : "ear_reservatorio_subsistema_proprio_mwmes", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "ear_reservatorio_subsistema_jusante_mwmes", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "earmax_reservatorio_subsistema_proprio_mwmes", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "earmax_reservatorio_subsistema_jusante_mwmes", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "val_contribearmaxbacia", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "val_contribearsubsistema", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "val_contribearmaxsubsistema", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "val_contribearsubsistemajusante", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "val_contribearmaxsubsistemajusante", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "val_contribearmaxsin", "type" : "FLOAT", "mode" : "REQUIRED" },
    { "name" : "file_source", "type" : "STRING", "mode" : "NULLABLE" },
    { "name" : "ingestion_timestamp", "type" : "TIMESTAMP", "mode" : "NULLABLE" }
  ])

  depends_on = [google_project_service.apis]
}

# Service Account específica para ENA
resource "google_service_account" "sa_ena_pipeline" {
  account_id   = "sa-ena-pipeline"
  display_name = "Service Account para Pipeline ENA"

  depends_on = [google_project_service.apis]
}

# Permissões específicas para a SA do ENA
resource "google_project_iam_member" "ena_storage_access" {
  project = "project-sauter-hydro-forecast"
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${google_service_account.sa_ena_pipeline.email}"
}

resource "google_bigquery_dataset_iam_member" "ena_bq_access" {
  dataset_id = google_bigquery_dataset.ena_dataset.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.sa_ena_pipeline.email}"
}

resource "google_project_iam_member" "ena_secret_access" {
  project = "project-sauter-hydro-forecast"
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.sa_ena_pipeline.email}"
}

# Cloud Scheduler para executar o pipeline diariamente
resource "google_cloud_scheduler_job" "ena_daily_job" {
  name             = "ena-daily-processing"
  description      = "Executa processamento ENA diariamente"
  schedule         = "0 6 * * *"
  time_zone        = "America/Sao_Paulo"
  attempt_deadline = "600s"

  http_target {
    http_method = "POST"
    uri         = "https://us-central1-project-sauter-hydro-forecast.cloudfunctions.net/ena-data-processor"

    oidc_token {
      service_account_email = google_service_account.sa_ena_pipeline.email
    }
  }

  depends_on = [google_project_service.apis]
}

# Outputs adicionais para ENA
output "ena_table_id" {
  description = "ID da tabela ENA"
  value       = google_bigquery_table.ena_consolidado.table_id
}

output "ena_service_account_email" {
  description = "Email da Service Account ENA"
  value       = google_service_account.sa_ena_pipeline.email
}