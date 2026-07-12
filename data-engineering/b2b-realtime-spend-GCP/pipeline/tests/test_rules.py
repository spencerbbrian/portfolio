"""
test_rules.py

Unit tests for the RuleCheckFn DoFn.

Each test passes a transaction dict directly to the DoFn and asserts that
the correct rule flags are set. No GCP, no emulator, no credentials.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from transforms.rules import RuleCheckFn


def make_txn(**overrides) -> dict:
    """Build a baseline normal transaction dict."""
    base = {
        "transaction_id": "test-uuid-001",
        "company_id": "company_0001",
        "vendor_id": "vendor_0001",
        "vendor_category": "saas_software",
        "vendor_risk_tier": "low",
        "amount_usd": 500.0,
        "baseline_monthly_spend": 50000.0,
        "timestamp": "2026-06-15T10:30:00+00:00",  # weekday, business hours
        "company_size_tier": "mid_market",
        "company_name": "Test Corp",
        "vendor_name": "Test Vendor",
    }
    base.update(overrides)
    return base


class TestRuleCheckFn:

    def _process(self, txn: dict) -> dict:
        """Helper: run one transaction through RuleCheckFn and return result."""
        fn = RuleCheckFn()
        results = list(fn.process(txn))
        assert len(results) == 1
        return results[0]

    def test_normal_transaction_no_flags(self):
        """A normal transaction should have no rule flags set."""
        result = self._process(make_txn())
        assert result["rule_spend_spike"] is False
        assert result["rule_high_risk_vendor"] is False
        assert result["rule_off_hours"] is False
        assert result["rule_round_amount"] is False
        assert result["rule_flag_count"] == 0
        assert result["any_rule_triggered"] is False

    def test_spend_spike_flag(self):
        """
        Amount > 5x the expected per-transaction mean should trigger spend_spike.
        Expected mean = baseline * 0.01 = 50000 * 0.01 = 500.
        Spike threshold = 500 * 5 = 2500.
        """
        result = self._process(make_txn(amount_usd=10000.0))
        assert result["rule_spend_spike"] is True
        assert result["rule_flag_count"] >= 1

    def test_no_spend_spike_below_threshold(self):
        """Amount just below the spike threshold should not trigger."""
        result = self._process(make_txn(amount_usd=2499.0))
        assert result["rule_spend_spike"] is False

    def test_high_risk_vendor_large_amount(self):
        """High risk vendor + amount above $5000 should trigger."""
        result = self._process(make_txn(
            vendor_risk_tier="high",
            amount_usd=6000.0
        ))
        assert result["rule_high_risk_vendor"] is True

    def test_high_risk_vendor_small_amount_no_flag(self):
        """High risk vendor + small amount should NOT trigger."""
        result = self._process(make_txn(
            vendor_risk_tier="high",
            amount_usd=100.0
        ))
        assert result["rule_high_risk_vendor"] is False

    def test_off_hours_flag(self):
        """Transaction at 3am should trigger off_hours rule."""
        result = self._process(make_txn(
            timestamp="2026-06-15T03:15:00+00:00"
        ))
        assert result["rule_off_hours"] is True

    def test_business_hours_no_off_hours_flag(self):
        """Transaction at 10am should not trigger off_hours."""
        result = self._process(make_txn(
            timestamp="2026-06-15T10:00:00+00:00"
        ))
        assert result["rule_off_hours"] is False

    def test_round_amount_flag(self):
        """Exactly $10,000 should trigger round_amount rule."""
        result = self._process(make_txn(amount_usd=10000.0))
        assert result["rule_round_amount"] is True

    def test_non_round_amount_no_flag(self):
        """$10,001 should not trigger round_amount."""
        result = self._process(make_txn(amount_usd=10001.0))
        assert result["rule_round_amount"] is False

    def test_multiple_rules_can_fire_together(self):
        """Multiple rules should fire simultaneously and count correctly."""
        result = self._process(make_txn(
            amount_usd=10000.0,           # round amount + spend spike
            timestamp="2026-06-15T03:00:00+00:00",  # off hours
        ))
        assert result["rule_flag_count"] >= 2
        assert result["any_rule_triggered"] is True

    def test_output_dict_has_all_expected_fields(self):
        """Result dict should contain all rule fields."""
        result = self._process(make_txn())
        expected_fields = [
            "rule_spend_spike",
            "rule_high_risk_vendor",
            "rule_off_hours",
            "rule_round_amount",
            "rule_flag_count",
            "any_rule_triggered",
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"