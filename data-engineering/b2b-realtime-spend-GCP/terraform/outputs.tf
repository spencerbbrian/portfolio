output "bq_dataset_raw" {
  value = google_bigquery_dataset.raw.dataset_id
}

output "bq_dataset_staging" {
  value = google_bigquery_dataset.staging.dataset_id
}

output "bq_dataset_marts" {
  value = google_bigquery_dataset.marts.dataset_id
}

output "model_artifact_bucket" {
  value = google_storage_bucket.model_artifacts.name
}

output "pubsub_topic" {
  value = google_pubsub_topic.transactions.name
}

output "pubsub_subscription" {
  value = google_pubsub_subscription.transactions_sub.name
}

output "pipeline_service_account_email" {
  value = google_service_account.pipeline_sa.email
}

output "retrain_function_url" {
  value = google_cloudfunctions2_function.retrain_trigger.url
}