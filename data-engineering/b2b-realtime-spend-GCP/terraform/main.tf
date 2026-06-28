# -----------------------------------------------------------------------------
# Enable required APIs
# -----------------------------------------------------------------------------
locals {
  required_apis = [
    "bigquery.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "dataflow.googleapis.com",
    "iam.googleapis.com",
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each = toset(local.required_apis)
  project  = var.project_id
  service  = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# -----------------------------------------------------------------------------
# Service account used by the pipeline (Dataflow workers, Cloud Functions)
# -----------------------------------------------------------------------------
resource "google_service_account" "pipeline_sa" {
  account_id   = var.pipeline_service_account_id
  display_name = "B2B Spend Analytics Pipeline SA"
  project      = var.project_id

  depends_on = [google_project_service.enabled_apis]
}

resource "google_project_iam_member" "pipeline_sa_bq" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

resource "google_project_iam_member" "pipeline_sa_bq_jobuser" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

resource "google_project_iam_member" "pipeline_sa_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

resource "google_project_iam_member" "pipeline_sa_gcs" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

resource "google_project_iam_member" "pipeline_sa_dataflow" {
  project = var.project_id
  role    = "roles/dataflow.worker"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# -----------------------------------------------------------------------------
# BigQuery datasets
# -----------------------------------------------------------------------------
resource "google_bigquery_dataset" "raw" {
  dataset_id  = var.bq_dataset_raw
  project     = var.project_id
  location    = var.region
  description = "Raw + ML-scored B2B transactions written by the Beam/Dataflow pipeline"
  delete_contents_on_destroy = true

  labels = {
    environment = var.environment
  }

  depends_on = [google_project_service.enabled_apis]
}

resource "google_bigquery_dataset" "staging" {
  dataset_id  = var.bq_dataset_staging
  project     = var.project_id
  location    = var.region
  description = "dbt staging models"
  delete_contents_on_destroy = true

  labels = {
    environment = var.environment
  }

  depends_on = [google_project_service.enabled_apis]
}

resource "google_bigquery_dataset" "marts" {
  dataset_id  = var.bq_dataset_marts
  project     = var.project_id
  location    = var.region
  description = "dbt mart models (fraud alerts, company spend summary, vendor risk)"
  delete_contents_on_destroy = true

  labels = {
    environment = var.environment
  }

  depends_on = [google_project_service.enabled_apis]
}

# -----------------------------------------------------------------------------
# GCS bucket — deployed model artifact storage (mirrors fake-gcs-server locally)
# -----------------------------------------------------------------------------
resource "google_storage_bucket" "model_artifacts" {
  name                        = var.model_artifact_bucket_name
  project                     = var.project_id
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true # convenient for a portfolio project; remove if you want safer deletes

  versioning {
    enabled = true
  }

  labels = {
    environment = var.environment
  }

  depends_on = [google_project_service.enabled_apis]
}

# -----------------------------------------------------------------------------
# Real Pub/Sub — used only for deploy/demo bursts, not local dev
# -----------------------------------------------------------------------------
resource "google_pubsub_topic" "transactions" {
  name    = var.pubsub_topic_name
  project = var.project_id

  labels = {
    environment = var.environment
  }

  depends_on = [google_project_service.enabled_apis]
}

resource "google_pubsub_subscription" "transactions_sub" {
  name    = var.pubsub_subscription_name
  project = var.project_id
  topic   = google_pubsub_topic.transactions.name

  ack_deadline_seconds       = 60
  message_retention_duration = "86400s" # 1 day

  labels = {
    environment = var.environment
  }
}

# -----------------------------------------------------------------------------
# Cloud Functions + Cloud Scheduler — retrain / dbt-run trigger
# -----------------------------------------------------------------------------
resource "google_storage_bucket" "function_source" {
  name                        = "${var.project_id}-cf-source"
  project                     = var.project_id
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true

  depends_on = [google_project_service.enabled_apis]
}

# This zips cloud_functions/retrain_trigger/ (main.py + requirements.txt)
# automatically every time you run `terraform apply` — no manual zip step.
data "archive_file" "retrain_function_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../cloud_functions/retrain_trigger"
  output_path = "${path.module}/.tmp/retrain_trigger_source.zip"
}

resource "google_storage_bucket_object" "retrain_function_zip" {
  name   = "retrain_trigger_source_${data.archive_file.retrain_function_zip.output_md5}.zip"
  bucket = google_storage_bucket.function_source.name
  source = data.archive_file.retrain_function_zip.output_path
}

resource "google_cloudfunctions2_function" "retrain_trigger" {
  name     = var.retrain_function_name
  project  = var.project_id
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "main" # adjust to match your function's entry point
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.retrain_function_zip.name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    available_memory      = "256M"
    timeout_seconds        = 300
    service_account_email = google_service_account.pipeline_sa.email
  }

  depends_on = [google_project_service.enabled_apis]
}

resource "google_cloud_scheduler_job" "retrain_schedule" {
  name      = "${var.retrain_function_name}-schedule"
  project   = var.project_id
  region    = var.region
  schedule  = var.retrain_schedule_cron
  time_zone = "Etc/UTC"

  http_target {
    uri         = google_cloudfunctions2_function.retrain_trigger.url
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.pipeline_sa.email
    }
  }

  depends_on = [google_project_service.enabled_apis]
}