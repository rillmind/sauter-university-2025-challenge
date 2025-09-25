output "project_id" {
  description = "ID do projeto"
  value       = data.google_project.project.project_id
}

output "project_number" {
  description = "Número do projeto"
  value       = data.google_project.project.number
}

output "workload_identity_provider" {
  description = "Provider para GitHub"
  value       = "projects/${data.google_project.project.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id}"
}

output "github_service_account_email" {
  description = "Email da SA do GitHub"
  value       = google_service_account.github_actions_sa.email
}