"""
test_model_sanity.py

Sanity checks for the trained Isolation Forest model.

These tests load the actual saved model artifact (from local path,
not GCS — CI has the repo checked out so the model can be committed
or regenerated as part of CI). They verify the model behaves as expected:
anomalous transactions should score lower (more negative) than normal ones.

If the model artifact doesn't exist (first CI run, or after terraform destroy
wiped GCS), the test is skipped gracefully rather than failing the whole suite.
"""

import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'ml'))

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'model_artifacts', 'isolation_forest_v1.joblib')


def build_feature_vector(amount_usd, baseline, hour=10, dow=1,
                          vendor_category="saas_software",
                          vendor_risk_tier="low"):
    """Build a feature vector matching feature_engineering.py's output."""
    import math
    from feature_engineering import CATEGORY_TO_INT

    return [
        amount_usd,
        amount_usd / baseline if baseline > 0 else 0.0,
        math.log1p(amount_usd),
        hour,
        dow,
        int(dow >= 5),
        int(vendor_risk_tier == "high"),
        CATEGORY_TO_INT.get(vendor_category, 0),
    ]


@pytest.fixture(scope="module")
def model():
    """Load the model once for all tests in this module."""
    if not os.path.exists(MODEL_PATH):
        pytest.skip(
            f"Model artifact not found at {MODEL_PATH}. "
            f"Run ml/train_isolation_forest.py first."
        )
    import joblib
    return joblib.load(MODEL_PATH)


class TestModelSanity:

    def test_model_scores_normal_transaction_higher_than_anomaly(self, model):
        """
        Normal transactions should have higher (less negative) scores than
        obvious anomalies. This is the core behavioural guarantee.
        """
        baseline = 50_000.0

        # Typical normal transaction: ~1% of monthly baseline, business hours
        normal = build_feature_vector(
            amount_usd=500.0,
            baseline=baseline,
            hour=10,
            dow=1,
        )

        # Obvious anomaly: 20x the expected transaction mean
        anomaly = build_feature_vector(
            amount_usd=100_000.0,
            baseline=baseline,
            hour=3,   # off hours too
            dow=6,    # weekend
        )

        normal_score = model.score_samples([normal])[0]
        anomaly_score = model.score_samples([anomaly])[0]

        assert normal_score > anomaly_score, (
            f"Expected normal score ({normal_score:.4f}) > "
            f"anomaly score ({anomaly_score:.4f})"
        )

    def test_model_predict_returns_valid_labels(self, model):
        """model.predict() should return only 1 (normal) or -1 (anomaly)."""
        baseline = 50_000.0
        vectors = [
            build_feature_vector(500.0, baseline),
            build_feature_vector(100_000.0, baseline),
            build_feature_vector(250.0, baseline),
        ]
        predictions = model.predict(vectors)
        for pred in predictions:
            assert pred in [1, -1], f"Unexpected prediction: {pred}"

    def test_model_score_samples_returns_floats_in_expected_range(self, model):
        """score_samples() should return floats roughly in [-0.6, 0.2]."""
        baseline = 50_000.0
        vectors = [build_feature_vector(500.0, baseline) for _ in range(10)]
        scores = model.score_samples(vectors)
        for score in scores:
            assert -1.0 < score < 0.5, (
                f"Score {score} is outside the expected range — "
                f"model may have been trained on wrong data."
            )

    def test_model_handles_batch_input(self, model):
        """Model should handle multiple records at once without errors."""
        baseline = 50_000.0
        vectors = [build_feature_vector(float(i * 100), baseline) for i in range(1, 11)]
        scores = model.score_samples(vectors)
        assert len(scores) == 10