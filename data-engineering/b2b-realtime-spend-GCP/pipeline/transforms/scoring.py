"""
scoring.py

ML scoring transform. Loads the trained Isolation Forest model from GCS
(fake-gcs-server locally, real GCS when deployed) once per worker in setup(),
then applies it to each transaction in process().

Why load in setup() and not __init__():
    __init__() runs when the DoFn object is constructed on the driver (the
    machine running your pipeline code). setup() runs once per worker process
    after Beam has serialized and distributed the DoFn to wherever it's
    actually executing. Loading in setup() means:
        - The model artifact travels from GCS to the worker, not from your
          laptop to every worker.
        - The model is loaded once per worker, not once per record (which
          would be catastrophically slow).
        - It works correctly for both DirectRunner (local) and DataflowRunner
          (cloud workers).

Final risk score logic:
    - ML anomaly score from Isolation Forest: ranges from ~-0.5 (anomalous)
      to ~0.1 (normal). We normalise this to 0–1 where 1 = most anomalous.
    - Rule flag contribution: each rule that fires adds 0.2 to the score,
      capped at 0.4 total from rules (so rules alone can't push to 1.0,
      and ML alone can't be fully overridden by rules either).
    - final_risk_score = min(1.0, ml_score_normalised + rule_contribution)
    - risk_flag = final_risk_score >= 0.5
"""

import logging
import os
import tempfile

import apache_beam as beam
import joblib
import numpy as np
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env.local"))

MODEL_FILENAME = "isolation_forest_v1.joblib"

# GCS config — reads from env vars set in .env.local
LOCAL_GCS_ENDPOINT = os.getenv("STORAGE_EMULATOR_HOST", "http://localhost:4443")
LOCAL_PROJECT_ID = os.getenv("LOCAL_PROJECT_ID", "local-dev-project")
REAL_PROJECT_ID = os.getenv("REAL_PROJECT_ID", "portfolio-analytics-499108")
MODEL_BUCKET_LOCAL = os.getenv("MODEL_ARTIFACT_BUCKET", "b2b-spend-models")
MODEL_BUCKET_REAL = os.getenv(
    "MODEL_ARTIFACT_BUCKET_REAL", "b2b-rtsg-model-artifacts-spencer"
)

# Risk thresholds
RISK_FLAG_THRESHOLD = 0.5       # final_risk_score >= this → risk_flag = True
RULE_CONTRIBUTION_PER_FLAG = 0.2  # each rule adds this much to the score
MAX_RULE_CONTRIBUTION = 0.4       # rules can contribute at most this much total


def _normalise_if_score(raw_score: float) -> float:
    """
    Convert Isolation Forest score_samples() output to a 0–1 anomaly score
    where 1 = most anomalous.

    Isolation Forest returns scores typically in the range [-0.5, 0.1].
    We clamp to [-0.5, 0.1] then invert and scale to [0, 1].
    """
    clamped = max(-0.5, min(0.1, raw_score))
    # Map [-0.5, 0.1] → [1.0, 0.0] (invert so anomalous = high score)
    normalised = 1.0 - ((clamped + 0.5) / 0.6)
    return round(normalised, 4)


class MLScoringFn(beam.DoFn):
    """
    DoFn that applies the Isolation Forest model to each transaction.

    Adds the following fields:
        ml_raw_score (float):         raw score_samples() output from the model
        ml_anomaly_score (float):     normalised 0–1 score (1 = most anomalous)
        rule_contribution (float):    score added by rule flags
        final_risk_score (float):     combined score, capped at 1.0
        risk_flag (bool):             True if final_risk_score >= threshold
    """

    def __init__(self, use_real_gcs: bool = False):
        self.use_real_gcs = use_real_gcs
        self.model = None  # loaded in setup(), not here

    def setup(self):
        """
        Called once per worker process before any elements are processed.
        Downloads the model artifact from GCS and loads it with joblib.
        """
        import sys

        # Add the ml/ directory to the path so we can import feature_engineering
        ml_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ml")
        if ml_dir not in sys.path:
            sys.path.append(ml_dir)

        from google.cloud import storage

        if self.use_real_gcs:
            os.environ.pop("STORAGE_EMULATOR_HOST", None)
            client = storage.Client(project=REAL_PROJECT_ID)
            bucket_name = MODEL_BUCKET_REAL
        else:
            client = storage.Client(
                project=LOCAL_PROJECT_ID,
                client_options={"api_endpoint": LOCAL_GCS_ENDPOINT},
            )
            bucket_name = MODEL_BUCKET_LOCAL

        logging.info(f"Loading model from gs://{bucket_name}/{MODEL_FILENAME}")

        bucket = client.bucket(bucket_name)
        blob = bucket.blob(MODEL_FILENAME)

        # Download to a temp file — joblib needs a file path, not a stream
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            tmp_path = tmp.name

        blob.download_to_filename(tmp_path)
        self.model = joblib.load(tmp_path)
        os.unlink(tmp_path)

        logging.info("Isolation Forest model loaded successfully.")

    def process(self, txn: dict, *args, **kwargs):
        import sys

        ml_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ml")
        if ml_dir not in sys.path:
            sys.path.append(ml_dir)

        from feature_engineering import engineer_features, features_to_vector

        try:
            features = engineer_features(txn)
            vector = features_to_vector(features)
            X = np.array([vector])

            # score_samples returns one value per row — take the first
            raw_score = float(self.model.score_samples(X)[0])
            ml_anomaly_score = _normalise_if_score(raw_score)

        except Exception as e:
            logging.warning(f"ML scoring failed for {txn.get('transaction_id')}: {e}")
            raw_score = 0.0
            ml_anomaly_score = 0.0

        # Rule contribution: each fired rule adds 0.2, max 0.4
        rule_flag_count = int(txn.get("rule_flag_count", 0))
        rule_contribution = min(
            rule_flag_count * RULE_CONTRIBUTION_PER_FLAG,
            MAX_RULE_CONTRIBUTION,
        )

        final_risk_score = round(min(1.0, ml_anomaly_score + rule_contribution), 4)
        risk_flag = final_risk_score >= RISK_FLAG_THRESHOLD

        yield {
            **txn,
            "ml_raw_score": round(raw_score, 6),
            "ml_anomaly_score": ml_anomaly_score,
            "rule_contribution": round(rule_contribution, 4),
            "final_risk_score": final_risk_score,
            "risk_flag": risk_flag,
        }