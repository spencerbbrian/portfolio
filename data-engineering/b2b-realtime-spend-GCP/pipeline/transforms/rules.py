"""
rules.py

Rule-based anomaly checks applied to each transaction before ML scoring.

Rules are deterministic — they fire reliably on known bad patterns and are
easy to explain. The ML model (Isolation
Forest) handles the unknown patterns that rules can't anticipate.

The two layers complement each other:
    - Rules: high precision on known patterns, zero false negatives for those
    - ML:    catches novel/subtle anomalies rules would miss

Each rule adds a flag to the transaction dict. The scoring transform later
combines these flags with the ML anomaly score into a single final_risk_score.

Rules implemented:
    1. spend_spike:        amount > N std devs above company's expected mean
    2. high_risk_vendor:   vendor_risk_tier == "high" AND amount above threshold
    3. off_hours:          transaction at 00:00–05:00 local time (UTC proxy)
    4. round_amount:       amount is suspiciously round (e.g. exactly $10,000)
"""

import logging
import math
from datetime import datetime

import apache_beam as beam


# How many standard deviations above the expected mean before we flag
# spend_spike. The expected mean per transaction is ~1% of monthly baseline
# (as set in the producer). We flag at 5x that mean as a conservative
# threshold — real tuning would use historical data.
SPEND_SPIKE_MULTIPLIER = 5.0

# Minimum amount (USD) for a high-risk vendor transaction to be flagged.
# A $5 charge to a high-risk vendor is probably fine; $50,000 is not.
HIGH_RISK_VENDOR_THRESHOLD = 5_000.0

# Off-hours window (UTC). Real implementations would use company timezone;
# we use UTC as a proxy since our simulated companies are global.
OFF_HOURS_START = 0   # midnight
OFF_HOURS_END = 5     # 5am


def _is_spend_spike(txn: dict) -> bool:
    """
    Flag if amount is more than SPEND_SPIKE_MULTIPLIER times the expected
    per-transaction mean for this company.

    Expected mean = baseline_monthly_spend * 0.01 (matches producer logic).
    """
    baseline = float(txn.get("baseline_monthly_spend", 0))
    if baseline <= 0:
        return False
    expected_mean = baseline * 0.01
    return float(txn["amount_usd"]) > expected_mean * SPEND_SPIKE_MULTIPLIER


def _is_high_risk_vendor_large_amount(txn: dict) -> bool:
    """Flag if vendor is high-risk AND the amount exceeds the threshold."""
    return (
        txn.get("vendor_risk_tier") == "high"
        and float(txn["amount_usd"]) > HIGH_RISK_VENDOR_THRESHOLD
    )


def _is_off_hours(txn: dict) -> bool:
    """Flag if transaction timestamp falls in the off-hours window."""
    try:
        ts_raw = txn["timestamp"]
        if ts_raw.endswith("Z"):
            ts_raw = ts_raw[:-1] + "+00:00"
        ts = datetime.fromisoformat(ts_raw)
        return OFF_HOURS_START <= ts.hour < OFF_HOURS_END
    except Exception:
        return False


def _is_round_amount(txn: dict) -> bool:
    """
    Flag suspiciously round amounts — e.g. exactly $5,000, $10,000, $50,000.
    Real fraud sometimes uses round numbers for ease of bookkeeping.
    We check if the amount is a multiple of 1000 and above $5,000.
    """
    amount = float(txn["amount_usd"])
    return amount >= 5_000 and amount % 1_000 == 0


class RuleCheckFn(beam.DoFn):
    """
    DoFn that applies all rule-based checks to a valid transaction dict.

    Adds the following fields to the dict:
        rule_spend_spike (bool)
        rule_high_risk_vendor (bool)
        rule_off_hours (bool)
        rule_round_amount (bool)
        rule_flag_count (int): how many rules fired — used in final scoring
        any_rule_triggered (bool): True if at least one rule fired

    Yields the enriched transaction dict — no branching output here, all
    records continue downstream regardless of whether rules fired.
    """

    def process(self, txn: dict, *args, **kwargs):
        spend_spike = _is_spend_spike(txn)
        high_risk_vendor = _is_high_risk_vendor_large_amount(txn)
        off_hours = _is_off_hours(txn)
        round_amount = _is_round_amount(txn)

        rule_flag_count = sum([spend_spike, high_risk_vendor, off_hours, round_amount])

        enriched = {
            **txn,
            "rule_spend_spike": spend_spike,
            "rule_high_risk_vendor": high_risk_vendor,
            "rule_off_hours": off_hours,
            "rule_round_amount": round_amount,
            "rule_flag_count": rule_flag_count,
            "any_rule_triggered": rule_flag_count > 0,
        }

        if rule_flag_count > 0:
            logging.info(
                f"Rules fired ({rule_flag_count}) on {txn['transaction_id']} "
                f"| company: {txn['company_id']} | amount: ${txn['amount_usd']}"
            )

        yield enriched