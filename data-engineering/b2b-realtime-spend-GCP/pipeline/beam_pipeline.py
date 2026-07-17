"""
beam_pipeline.py
 
Main Apache Beam pipeline. Reads transactions from Pub/Sub, processes them
through parsing → feature engineering → rule checks → ML scoring → windowing,
then writes results to BigQuery.
 
The same code runs locally with DirectRunner (against emulators) and on GCP
with DataflowRunner (against real services). The only thing that changes is
the runner and the endpoint config, controlled via env vars and CLI flags.
 
Usage:
    # Local DirectRunner against emulators (default)
    python beam_pipeline.py
 
    # Real GCP Pub/Sub + real GCS model, still DirectRunner (hybrid test)
    python beam_pipeline.py --use-real-pubsub --use-real-gcs
 
    # Full Dataflow deploy (demo burst)
    python beam_pipeline.py --runner DataflowRunner --use-real-pubsub --use-real-gcs
 
BigQuery tables written:
    b2b_spend_raw.transactions_scored  — one row per transaction, with risk score
    b2b_spend_raw.company_spend_windows — one row per company per 5-min window
"""

import argparse
import logging
import os
import sys

import apache_beam as beam
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition
from apache_beam.options.pipeline_options import (
    PipelineOptions,
    StandardOptions,
    GoogleCloudOptions,
    SetupOptions,
)
from dotenv import load_dotenv

# Path Setup for local imports
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(PIPELINE_DIR, "..")
sys.path.extend([PIPELINE_DIR, ROOT_DIR, os.path.join(ROOT_DIR, "ml")])

load_dotenv(os.path.join(ROOT_DIR, ".env.local"))

from transforms.parsing import ParseTransactionFn, VALID_TAG, DEAD_LETTER_TAG
from transforms.rules import RuleCheckFn   
from transforms.scoring import MLScoringFn                                      
from transforms.windowing import build_windowed_aggregates                      

# Config from env
LOCAL_PROJECT_ID = os.getenv("LOCAL_PROJECT_ID", "local-dev-project")
REAL_PROJECT_ID = os.getenv("REAL_PROJECT_ID")
PUBSUB_EMULATOR_HOST = os.getenv("PUBSUB_EMULATOR_HOST", "localhost:8085")
 
BQ_DATASET_RAW = os.getenv("BQ_DATASET_RAW", "b2b_spend_raw")
BQ_TRANSACTIONS_TABLE = "transactions_scored"
BQ_WINDOWS_TABLE = "company_spend_windows"
 
DEAD_LETTER_DIR = os.path.join(ROOT_DIR, "dead_letter")

# Big Query Schemas
TRANSACTIONS_SCHEMA = {
    "fields": [
        {"name": "transaction_id",           "type": "STRING",  "mode": "REQUIRED"},
        {"name": "company_id",               "type": "STRING",  "mode": "REQUIRED"},
        {"name": "company_name",             "type": "STRING",  "mode": "NULLABLE"},
        {"name": "company_size_tier",        "type": "STRING",  "mode": "NULLABLE"},
        {"name": "vendor_id",                "type": "STRING",  "mode": "NULLABLE"},
        {"name": "vendor_name",              "type": "STRING",  "mode": "NULLABLE"},
        {"name": "vendor_category",          "type": "STRING",  "mode": "NULLABLE"},
        {"name": "vendor_risk_tier",         "type": "STRING",  "mode": "NULLABLE"},
        {"name": "amount_usd",               "type": "FLOAT",   "mode": "REQUIRED"},
        {"name": "currency",                 "type": "STRING",  "mode": "NULLABLE"},
        {"name": "payment_method",           "type": "STRING",  "mode": "NULLABLE"},
        {"name": "department",               "type": "STRING",  "mode": "NULLABLE"},
        {"name": "timestamp",                "type": "STRING",  "mode": "NULLABLE"},
        {"name": "is_anomaly",               "type": "BOOLEAN", "mode": "NULLABLE"},
        {"name": "anomaly_type",             "type": "STRING",  "mode": "NULLABLE"},
        {"name": "rule_spend_spike",         "type": "BOOLEAN", "mode": "NULLABLE"},
        {"name": "rule_high_risk_vendor",    "type": "BOOLEAN", "mode": "NULLABLE"},
        {"name": "rule_off_hours",           "type": "BOOLEAN", "mode": "NULLABLE"},
        {"name": "rule_round_amount",        "type": "BOOLEAN", "mode": "NULLABLE"},
        {"name": "rule_flag_count",          "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "any_rule_triggered",       "type": "BOOLEAN", "mode": "NULLABLE"},
        {"name": "ml_raw_score",             "type": "FLOAT",   "mode": "NULLABLE"},
        {"name": "ml_anomaly_score",         "type": "FLOAT",   "mode": "NULLABLE"},
        {"name": "rule_contribution",        "type": "FLOAT",   "mode": "NULLABLE"},
        {"name": "final_risk_score",         "type": "FLOAT",   "mode": "NULLABLE"},
        {"name": "risk_flag",                "type": "BOOLEAN", "mode": "NULLABLE"},
        {"name": "baseline_monthly_spend",   "type": "FLOAT",   "mode": "NULLABLE"},
    ]
}
 
WINDOWS_SCHEMA = {
    "fields": [
        {"name": "window_start",         "type": "STRING",  "mode": "REQUIRED"},
        {"name": "window_end",           "type": "STRING",  "mode": "REQUIRED"},
        {"name": "company_id",           "type": "STRING",  "mode": "REQUIRED"},
        {"name": "company_name",         "type": "STRING",  "mode": "NULLABLE"},
        {"name": "company_size_tier",    "type": "STRING",  "mode": "NULLABLE"},
        {"name": "transaction_count",    "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "total_amount_usd",     "type": "FLOAT",   "mode": "NULLABLE"},
        {"name": "max_amount_usd",       "type": "FLOAT",   "mode": "NULLABLE"},
        {"name": "avg_amount_usd",       "type": "FLOAT",   "mode": "NULLABLE"},
        {"name": "risk_flagged_count",   "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "any_risk_flag",        "type": "BOOLEAN", "mode": "NULLABLE"},
    ]
}

# Dead letter sink (local file during dev)
class WriteDeadLetterFn(beam.DoFn):
    """
    Writes dead-lettered records to a local file for inspection during dev.
    In production this would write to a GCS bucket or a BigQuery table.
    """
 
    def setup(self):
        os.makedirs(DEAD_LETTER_DIR, exist_ok=True)
        self.output_path = os.path.join(DEAD_LETTER_DIR, "dead_letter.jsonl")
 
    def process(self, record, *args, **kwargs):
        import json
        with open(self.output_path, "a") as f:
            f.write(json.dumps(record) + "\n")
        logging.warning(f"Dead-letter written: {record.get('error', 'unknown error')}")
        yield record

# Pipeline definition
def build_pipeline_options(args: argparse.Namespace) -> PipelineOptions:
    """
    Build Beam pipeline options based on CLI args and env vars.
    DirectRunner requires very few options; DataflowRunner needs more.
    """

    project_id = REAL_PROJECT_ID if args.use_real_pubsub else LOCAL_PROJECT_ID
    pipeline_options_list = [
    f"--runner={args.runner}",
    f"--project={project_id}",
    f"--region={os.getenv('GCP_REGION', 'europe-west1')}",
    "--streaming",
    "--direct_num_workers=4",
    "--direct_running_mode=multi_threading",
    "--temp_location=/tmp/beam_temp",
    ]
    options = PipelineOptions(pipeline_options_list)
    return options

def run(args: argparse.Namespace) -> None:
    project_id = REAL_PROJECT_ID if args.use_real_pubsub else LOCAL_PROJECT_ID
    bq_project = REAL_PROJECT_ID #always use BigQuery

    if args.use_real_pubsub:
        subscription = f"projects/{REAL_PROJECT_ID}/subscriptions/b2b-transactions-sub"
        os.environ.pop("PUBSUB_EMULATOR_HOST", None)  # unset emulator host
        logging.info(f"Using real Pub/Sub subscription: {subscription}")
    else:
        subscription = f"projects/{LOCAL_PROJECT_ID}/subscriptions/b2b-transactions-sub"
        os.environ["PUBSUB_EMULATOR_HOST"] = PUBSUB_EMULATOR_HOST
        logging.info(f"Using Pub/Sub emulator at {subscription}")

    # Bigquery table references
    txn_table = f"{bq_project}:{BQ_DATASET_RAW}.{BQ_TRANSACTIONS_TABLE}"
    win_table = f"{bq_project}:{BQ_DATASET_RAW}.{BQ_WINDOWS_TABLE}"

    options = build_pipeline_options(args)

    with beam.Pipeline(options=options) as p:
        # Read from Pub/Sub
        raw_messages = (
            p
            | "ReadFromPubSub" >> beam.io.ReadFromPubSub(
                subscription=subscription
            )
        )

        # Parse & Validate
        parsed = (
            raw_messages
            | "ParseTransactions" >> beam.ParDo(
                ParseTransactionFn()
            ).with_outputs(VALID_TAG, DEAD_LETTER_TAG)
        )

        valid_transactions = parsed[VALID_TAG]
        dead_letters = parsed[DEAD_LETTER_TAG]

        # Dead-letter sink
        _ = (
            dead_letters
            | "WriteDeadLetter" >> beam.ParDo(WriteDeadLetterFn())
        )

        # Rule-based checks 
        rule_checked = (
            valid_transactions
            | "ApplyRules" >> beam.ParDo(RuleCheckFn())
        )

        # ML scoring
        scored = (
            rule_checked
            | "MLScoring" >> beam.ParDo(
                MLScoringFn(use_real_gcs=args.use_real_gcs)
            )
        )

        # Write scored transactions to BigQuery
        _ = (
            scored
            | "WriteScoredTxnsToBQ" >> WriteToBigQuery(
                table=txn_table,
                schema=TRANSACTIONS_SCHEMA,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED, # create table if it doesn't exist
            )
        )

        # Windowed aggregation branch
        windowed = build_windowed_aggregates(scored)

        # Write windowed aggregates to BigQuery
        _ = (
            windowed
            | "WriteWindowsToBQ" >> WriteToBigQuery(
                table=win_table,
                schema=WINDOWS_SCHEMA,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

    logging.info("Pipeline completed successfully.")


# Entry point
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(description="B2B Spend Analytics Beam Pipeline")
    parser.add_argument(
        "--runner",
        default="DirectRunner",
        choices=["DirectRunner", "DataflowRunner"],
        help="Beam runner to use (default: DirectRunner for local dev, DataflowRunner for GCP)",
    )
    parser.add_argument(
        "--use-real-pubsub",
        action="store_true",
        help="Use real Pub/Sub subscription instead of emulator (default: False)",
    )
    parser.add_argument(
        "--use-real-gcs",
        action="store_true",
        help="Use real GCS bucket for ML model instead of local gcs-server (default: False)",
    )
    args = parser.parse_args()

    run(args)