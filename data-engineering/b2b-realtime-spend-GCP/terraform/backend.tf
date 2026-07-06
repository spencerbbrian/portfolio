terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # ---------------------------------------------------------------------------
  # GCS backend for remote state.
  #
  # IMPORTANT (chicken-and-egg): the bucket referenced here must exist BEFORE
  # you run `terraform init`, because Terraform can't create the bucket it's
  # also trying to store its own state in.
  #
  # Create it once, manually, before first init:
  #
  #   gcloud storage buckets create gs://YOUR_TF_STATE_BUCKET_NAME \
  #     --project=YOUR_PROJECT_ID \
  #     --location=europe-west1 \
  #     --uniform-bucket-level-access
  #
  # Then fill in the bucket name below (or pass via `terraform init
  # -backend-config="bucket=YOUR_TF_STATE_BUCKET_NAME"` to avoid hardcoding it
  # in version control).
  # ---------------------------------------------------------------------------
  backend "gcs" {
    bucket = "b2b-rtsg-terraform"
    prefix = "b2b-spend-analytics/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}