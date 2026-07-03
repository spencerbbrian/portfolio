"""
generate_training_data.py

Generates a batch of "normal" historical transactions for training the
Isolation Forest model. This is intentionally separate from the live producer
— we want a clean, labelled dataset of normal behaviour to train on, not a
mix of real-time messages that might already contain anomalies.

The transactions generated here mirror the structure of what the producer
publishes, with two key differences:
    1. Timestamps are spread across the past 90 days (business hours only)
       so the model learns realistic time-of-day and day-of-week patterns.
    2. No anomalies are injected — this is pure "normal" data. The Isolation
       Forest is an unsupervised model that learns the shape of normal
       behaviour, so training on anomalies would corrupt that baseline.

Output: training_data.csv in the ml/ directory.
"""

import csv
import math
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Allow importing from the producer folder for reference data loading
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "producer"))

from generate_reference_data import VENDOR_CATEGORIES  # noqa: E402

NUM_TRANSACTIONS = 10_000
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "training_data.csv")
REFERENCE_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "producer")

DEPARTMENTS = [
    "engineering", "marketing", "finance", "hr",
    "operations", "sales", "legal", "it",
]
PAYMENT_METHODS = [
    "corporate_card", "ach_transfer", "wire_transfer", "direct_debit",
]


def load_csv(path: str) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def random_business_timestamp(days_back: int = 90) -> datetime:
    """
    Return a random timestamp within the past N days, biased toward
    business hours (08:00–18:00) on weekdays. This gives the model a
    realistic time distribution to learn from rather than uniform random noise.

    Roughly 80% of transactions fall in business hours on weekdays;
    20% are outside (evening, weekend) — matches B2B reality where some
    automated payments and international transactions happen off-hours.
    """
    now = datetime.now(timezone.utc)
    # Pick a random day within the window
    offset_days = random.randint(0, days_back)
    base = now - timedelta(days=offset_days)

    if random.random() < 0.80:
        # Business hours, weekday
        # Roll forward to the nearest weekday if we landed on a weekend
        while base.weekday() >= 5:
            base -= timedelta(days=1)
        hour = random.randint(8, 17)
        minute = random.randint(0, 59)
    else:
        # Off-hours or weekend — still realistic, just less common
        hour = random.choice(list(range(0, 8)) + list(range(18, 24)))
        minute = random.randint(0, 59)

    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def generate_normal_transaction(company: dict, vendors: list[dict]) -> dict:
    """
    Generate one normal transaction. Logic mirrors producer.py's
    generate_transaction() but with historical timestamps and no anomaly paths.
    """
    vendor = random.choice(vendors)

    mean_amount = float(company["baseline_monthly_spend"]) * 0.01
    amount = round(abs(random.gauss(mean_amount, mean_amount * 0.4)), 2)
    amount = max(amount, 10.0)

    ts = random_business_timestamp()

    return {
        "transaction_id": str(uuid.uuid4()),
        "company_id": company["company_id"],
        "company_name": company["name"],
        "company_size_tier": company["size_tier"],
        "baseline_monthly_spend": company["baseline_monthly_spend"],
        "vendor_id": vendor["vendor_id"],
        "vendor_name": vendor["name"],
        "vendor_category": vendor["category"],
        "vendor_risk_tier": vendor["risk_tier"],
        "amount_usd": amount,
        "currency": "USD",
        "payment_method": random.choice(PAYMENT_METHODS),
        "department": random.choice(DEPARTMENTS),
        "timestamp": ts.isoformat(),
        "is_anomaly": False,
    }


def main() -> None:
    companies_path = os.path.join(REFERENCE_DATA_DIR, "companies.csv")
    vendors_path = os.path.join(REFERENCE_DATA_DIR, "vendors.csv")

    companies = load_csv(companies_path)
    vendors = load_csv(vendors_path)

    print(f"Loaded {len(companies)} companies, {len(vendors)} vendors.")
    print(f"Generating {NUM_TRANSACTIONS} normal training transactions...")

    transactions = []
    for i in range(NUM_TRANSACTIONS):
        company = random.choice(companies)
        txn = generate_normal_transaction(company, vendors)
        transactions.append(txn)

        if (i + 1) % 1000 == 0:
            print(f"  {i + 1}/{NUM_TRANSACTIONS}")

    fieldnames = list(transactions[0].keys())
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

    print(f"\n✅ Wrote {len(transactions)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()