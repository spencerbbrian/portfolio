"""
test_scoring.py

Unit tests for the MLScoringFn DoFn.

We don't load a real model from GCS here — we mock the model loading
so tests run in CI without any GCP credentials or network calls.
The test focus is on the scoring logic (normalisation, risk score
combination, flag thresholds) not on the model itself.
"""

import sys
import os
from unittest.mock import MagicMock, patch
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'ml'))

from transforms.scoring import MLScoringFn, _normalise_if_score


def make_txn(**overrides) -> dict:
    """Build a transaction dict that's already been through RuleCheckFn."""
    base = {
        "transaction_id": "test-uuid-001",
        "company_id": "company_0001",
        "vendor_id": "vendor_0001",
        "vendor_category": "saas_software",
        "vendor_risk_tier": "low",
        "amount_usd": 500.0,
        "baseline_monthly_spend": 50000.0,
        "timestamp": "2026-06-15T10:30:00+00:00",
        "company_size_tier": "mid_market",
        "company_name": "Test Corp",
        "vendor_name": "Test Vendor",
        "rule_spend_spike": False,
        "rule_high_risk_vendor": False,
        "rule_off_hours": False,
        "rule_round_amount": False,
        "rule_flag_count": 0,
        "any_rule_triggered": False,
    }
    base.update(overrides)
    return base


class TestNormaliseIfScore:
    """Tests for the score normalisation utility."""

    def test_most_anomalous_score_normalises_to_near_one(self):
        """Score of -0.5 (most anomalous) should normalise to ~1.0."""
        result = _normalise_if_score(-0.5)
        assert result >= 0.95

    def test_most_normal_score_normalises_to_near_zero(self):
        """Score of 0.1 (most normal) should normalise to ~0.0."""
        result = _normalise_if_score(0.1)
        assert result <= 0.05

    def test_result_is_always_between_zero_and_one(self):
        """Normalised score must always be in [0, 1]."""
        for raw in [-0.6, -0.5, -0.3, -0.1, 0.0, 0.1, 0.2]:
            result = _normalise_if_score(raw)
            assert 0.0 <= result <= 1.0, f"Score {result} out of range for raw {raw}"


class TestMLScoringFn:

    def _make_fn_with_mock_model(self, mock_score: float) -> MLScoringFn:
        """
        Create an MLScoringFn with a fake model that returns a fixed score.
        This lets us test the scoring logic without loading a real model.
        """
        fn = MLScoringFn(use_real_gcs=False)
        mock_model = MagicMock()
        mock_model.score_samples.return_value = np.array([mock_score])
        fn.model = mock_model
        return fn

    def _process(self, fn: MLScoringFn, txn: dict) -> dict:
        results = list(fn.process(txn))
        assert len(results) == 1
        return results[0]

    def test_normal_transaction_low_risk_score(self):
        """Normal ML score + no rules = low final_risk_score."""
        fn = self._make_fn_with_mock_model(mock_score=0.05)  # very normal
        result = self._process(fn, make_txn())
        assert result["final_risk_score"] < 0.5
        assert result["risk_flag"] is False

    def test_anomalous_transaction_high_risk_score(self):
        """Anomalous ML score should push final_risk_score above threshold."""
        fn = self._make_fn_with_mock_model(mock_score=-0.45)  # very anomalous
        result = self._process(fn, make_txn())
        assert result["final_risk_score"] >= 0.5
        assert result["risk_flag"] is True

    def test_rules_add_to_risk_score(self):
        """Rule flags should increase the final_risk_score."""
        fn = self._make_fn_with_mock_model(mock_score=0.0)  # neutral ML score
        txn = make_txn(rule_flag_count=2, any_rule_triggered=True)
        result = self._process(fn, txn)
        # 2 rules × 0.2 = 0.4 rule contribution
        assert result["rule_contribution"] == 0.4

    def test_rule_contribution_capped_at_max(self):
        """Rule contribution should be capped at MAX_RULE_CONTRIBUTION (0.4)."""
        fn = self._make_fn_with_mock_model(mock_score=0.0)
        # 5 rules fired — contribution should still cap at 0.4
        txn = make_txn(rule_flag_count=5, any_rule_triggered=True)
        result = self._process(fn, txn)
        assert result["rule_contribution"] == 0.4

    def test_final_risk_score_capped_at_one(self):
        """final_risk_score should never exceed 1.0."""
        fn = self._make_fn_with_mock_model(mock_score=-0.5)  # max anomaly
        txn = make_txn(rule_flag_count=5, any_rule_triggered=True)
        result = self._process(fn, txn)
        assert result["final_risk_score"] <= 1.0

    def test_output_contains_all_scoring_fields(self):
        """Result should contain all expected scoring fields."""
        fn = self._make_fn_with_mock_model(mock_score=0.0)
        result = self._process(fn, make_txn())
        for field in ["ml_raw_score", "ml_anomaly_score", "rule_contribution",
                      "final_risk_score", "risk_flag"]:
            assert field in result, f"Missing field: {field}"