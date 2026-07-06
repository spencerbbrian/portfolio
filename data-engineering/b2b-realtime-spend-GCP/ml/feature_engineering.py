"""
feature_engineering.py

Builds the feature vector used by the Isolation Forest model.

This module is intentionally kept separate from both the training script and
the Beam pipeline so both can import the exact same logic. If you change a
feature here, it automatically changes in both places — keeping training and
inference consistent is one of the most common failure modes in ML pipelines.

Features used:
    - amount_usd: raw transaction amount
    - amount_to_baseline_ratio: how large this transaction is relative to the
      company's expected monthly spend. A ratio of 0.5 means the transaction
      is half the monthly baseline — suspicious for an SMB, normal for enterprise.
    - log_amount: log-scaled amount to reduce the effect of extreme outliers
      on the model during training
    - hour_of_day: 0–23, captures time-of-day patterns (e.g. transactions at
      3am are unusual for most B2B companies)
    - day_of_week: 0=Monday, 6=Sunday. B2B spend is heavily weekday-skewed.
    - is_weekend: binary flag derived from day_of_week, makes the weekend
      signal easier for the model to pick up without relying on the ordinal
      day_of_week value alone
    - is_high_risk_vendor: binary flag for vendor_risk_tier == "high"
    - vendor_category_encoded: integer encoding of vendor category. Not ideal
      (ordinal encoding implies ordering that doesn't exist) but sufficient for
      Isolation Forest which doesn't assume feature relationships the way a
      linear model would.
"""

import math
from datetime import datetime

# Must match VENDOR_CATEGORIES in generate_reference_data.py exactly —
# the encoding is positional, so order matters.
VENDOR_CATEGORIES = [
    "saas_software",
    "travel",
    "office_supplies",
    "payroll_services",
    "advertising_marketing",
    "professional_services",
    "logistics_shipping",
    "telecom_internet",
    "facilities_utilities",
    "hardware_equipment",
]

CATEGORY_TO_INT = {cat: i for i, cat in enumerate(VENDOR_CATEGORIES)}

FEATURE_NAMES = [
    "amount_usd",
    "amount_to_baseline_ratio",
    "log_amount",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_high_risk_vendor",
    "vendor_category_encoded",
]


def engineer_features(txn: dict) -> dict:
    """
    Take a raw transaction dict and return a flat dict of model features.

    The input dict must have at minimum:
        amount_usd, baseline_monthly_spend, timestamp,
        vendor_risk_tier, vendor_category

    Returns a dict keyed by FEATURE_NAMES. The Beam pipeline calls this on
    each message after parsing; the training script calls it on each row of
    the historical batch dataset.
    """
    amount = float(txn["amount_usd"])
    baseline = float(txn["baseline_monthly_spend"])

    # Parse timestamp — handle both Z suffix and +00:00 offset formats
    ts_raw = txn["timestamp"]
    if ts_raw.endswith("Z"):
        ts_raw = ts_raw[:-1] + "+00:00"
    ts = datetime.fromisoformat(ts_raw)

    hour = ts.hour
    dow = ts.weekday()  # 0=Monday, 6=Sunday

    vendor_category = txn.get("vendor_category", "saas_software")
    category_int = CATEGORY_TO_INT.get(vendor_category, 0)

    return {
        "amount_usd": amount,
        "amount_to_baseline_ratio": amount / baseline if baseline > 0 else 0.0,
        "log_amount": math.log1p(amount),  # log1p avoids log(0) for zero amounts
        "hour_of_day": hour,
        "day_of_week": dow,
        "is_weekend": int(dow >= 5),
        "is_high_risk_vendor": int(txn.get("vendor_risk_tier", "low") == "high"),
        "vendor_category_encoded": category_int,
    }


def features_to_vector(feature_dict: dict) -> list[float]:
    """
    Convert a feature dict (from engineer_features) into an ordered list of
    floats suitable for passing to scikit-learn.

    Keeps the column order consistent with FEATURE_NAMES so the model always
    sees features in the same positions it was trained on.
    """
    return [float(feature_dict[name]) for name in FEATURE_NAMES]