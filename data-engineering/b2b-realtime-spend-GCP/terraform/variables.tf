variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment label (dev/demo)"
  type        = string
  default     = "dev"
}

variable "model_artifact_bucket_name" {
  description = "GCS bucket name for the deployed ML model artifact (must be globally unique)"
  type        = string
}

variable "pubsub_topic_name" {
  description = "Real Pub/Sub topic name, used only for deploy/demo bursts"
  type        = string
  default     = "b2b-transactions"
}

variable "pubsub_subscription_name" {
  description = "Real Pub/Sub subscription name for the Beam/Dataflow pipeline"
  type        = string
  default     = "b2b-transactions-sub"
}

variable "bq_dataset_raw" {
  description = "BigQuery dataset for raw/scored transactions"
  type        = string
  default     = "b2b_spend_raw"
}

variable "bq_dataset_staging" {
  description = "BigQuery dataset for dbt staging models"
  type        = string
  default     = "b2b_spend_staging"
}

variable "bq_dataset_marts" {
  description = "BigQuery dataset for dbt mart models"
  type        = string
  default     = "b2b_spend_marts"
}

variable "retrain_function_name" {
  description = "Cloud Function name for the model retrain/dbt-run trigger"
  type        = string
  default     = "retrain-trigger"
}

variable "retrain_schedule_cron" {
  description = "Cron schedule for Cloud Scheduler to invoke the retrain trigger"
  type        = string
  default     = "0 6 * * *" # daily at 06:00
}

variable "pipeline_service_account_id" {
  description = "Service account ID (short name) used by the Beam/Dataflow pipeline and Cloud Functions"
  type        = string
  default     = "b2b-pipeline-sa"
}