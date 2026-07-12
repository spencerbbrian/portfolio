"""
main.py — Cloud Function: retrain_trigger

HTTP-triggered Cloud Function called daily by Cloud Scheduler.

What this does:
    1. Queries BigQuery to check if enough new transactions have arrived
       since the last retrain to justify retraining the model.
    2. If yes — triggers a Cloud Build job (or logs a retrain-needed signal
       that a CI/CD pipeline can pick up). For a portfolio project we log
       the signal to BigQuery rather than spinning up a full training cluster.
    3. Logs a summary row to a BigQuery audit table so you have a history
       of when retrains were triggered and why.

Why this is in Cloud Functions and not Airflow:
    Airflow runs locally on your Mac. When the pipeline is deployed to
    real Dataflow and running in the cloud, there's no local Airflow to
    orchestrate it. Cloud Scheduler + this function is the lightweight,
    always-on cloud-side equivalent — it costs effectively nothing
    (pay-per-invocation, one call per day = fractions of a cent/month).

Retrain logic:
    We retrain when transaction volume since the last retrain exceeds
    MIN_NEW_TRANSACTIONS_FOR_RETRAIN. For a portfolio project with simulated
    data, this threshold is intentionally low (500) so it triggers
    realistically during demos. A production system would use a more
    sophisticated drift detection signal.
"""

import functions_framework
import os
from datetime import datetime, timezone

from google.cloud import bigquery

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "portfolio-analytics-499108")
BQ_DATASET_RAW = os.environ.get("BQ_DATASET_RAW", "b2b_spend_raw")
BQ_DATASET_MARTS = os.environ.get("BQ_DATASET_MARTS", "b2b_spend_marts")

# Minimum number of new scored transactions since last retrain before we
# trigger a new model training run.
MIN_NEW_TRANSACTIONS_FOR_RETRAIN = 500


def get_transaction_count_since(client: bigquery.Client, since_timestamp: str) -> int:
    """Count transactions scored after a given timestamp."""
    query = f"""
        SELECT COUNT(*) as cnt
        FROM `{PROJECT_ID}.{BQ_DATASET_RAW}.transactions_scored`
        WHERE timestamp > '{since_timestamp}'
    """
    result = list(client.query(query).result())
    return result[0]["cnt"]


def get_last_retrain_timestamp(client: bigquery.Client) -> str:
    """
    Read the timestamp of the last retrain trigger from the audit log.
    Returns a far-past timestamp if the table doesn't exist yet (first run).
    """
    try:
        query = f"""
            SELECT MAX(triggered_at) as last_retrain
            FROM `{PROJECT_ID}.{BQ_DATASET_RAW}.retrain_audit_log`
        """
        result = list(client.query(query).result())
        last = result[0]["last_retrain"]
        if last is None:
            return "2000-01-01T00:00:00+00:00"
        return last.isoformat()
    except Exception:
        # Table doesn't exist yet — this is the first retrain trigger
        return "2000-01-01T00:00:00+00:00"


def log_retrain_event(
    client: bigquery.Client,
    triggered: bool,
    reason: str,
    new_txn_count: int,
) -> None:
    """Write a record to the retrain audit log in BigQuery."""
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "triggered_at": now,
            "retrain_triggered": triggered,
            "reason": reason,
            "new_transaction_count": new_txn_count,
        }
    ]

    table_ref = f"{PROJECT_ID}.{BQ_DATASET_RAW}.retrain_audit_log"

    # Create table if it doesn't exist
    schema = [
        bigquery.SchemaField("triggered_at", "TIMESTAMP"),
        bigquery.SchemaField("retrain_triggered", "BOOLEAN"),
        bigquery.SchemaField("reason", "STRING"),
        bigquery.SchemaField("new_transaction_count", "INTEGER"),
    ]

    table = bigquery.Table(table_ref, schema=schema)
    client.create_table(table, exists_ok=True)
    client.insert_rows_json(table_ref, rows)


@functions_framework.http
def main(request):
    """
    HTTP entry point. Called daily by Cloud Scheduler.
    Returns a JSON summary of what was checked and whether a retrain was triggered.
    """
    client = bigquery.Client(project=PROJECT_ID)
    now = datetime.now(timezone.utc).isoformat()

    try:
        # 1. When did we last retrain?
        last_retrain = get_last_retrain_timestamp(client)

        # 2. How many new transactions since then?
        new_count = get_transaction_count_since(client, last_retrain)

        # 3. Decide whether to trigger
        if new_count >= MIN_NEW_TRANSACTIONS_FOR_RETRAIN:
            reason = (
                f"{new_count} new transactions since last retrain "
                f"(threshold: {MIN_NEW_TRANSACTIONS_FOR_RETRAIN}). "
                f"Retrain recommended — run ml/train_isolation_forest.py "
                f"and upload the new artifact to GCS."
            )
            triggered = True
        else:
            reason = (
                f"Only {new_count} new transactions since last retrain "
                f"(threshold: {MIN_NEW_TRANSACTIONS_FOR_RETRAIN}). No retrain needed."
            )
            triggered = False

        # 4. Log to BigQuery audit table
        log_retrain_event(client, triggered, reason, new_count)

        response = {
            "status": "ok",
            "checked_at": now,
            "last_retrain_at": last_retrain,
            "new_transactions_since_last_retrain": new_count,
            "retrain_triggered": triggered,
            "reason": reason,
        }

        print(f"Retrain check complete: {response}")
        return response, 200

    except Exception as e:
        error_msg = f"Retrain trigger failed: {str(e)}"
        print(error_msg)
        return {"status": "error", "message": error_msg}, 500