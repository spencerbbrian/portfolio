"""
producer.py

Reads companies.csv and vendors.csv, generates realistic B2B transactions,
and publishes them as JSON messages to a Pub/Sub topic.

Defaults to the local Pub/Sub emulator. Pass --use-real-pubsub to point at
real GCP Pub/Sub instead (for deploy/demo bursts).

Usage:
    # Local emulator (default)
    python producer.py

    # With anomaly injection
    python producer.py --inject-anomalies

    # Against real GCP Pub/Sub
    python producer.py --use-real-pubsub

    # All options
    python producer.py --inject-anomalies --use-real-pubsub --delay 0.5
"""

import argparse
import csv
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from google.cloud import pubsub_v1

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv(".env.local")  # loads PUBSUB_EMULATOR_HOST if present in .env.local

# These match what you created in init_emulator.py and what Terraform created
# for the real GCP topic. The producer just points at whichever is active.
LOCAL_PROJECT_ID = os.getenv("LOCAL_PROJECT_ID", "local-dev-project")
REAL_PROJECT_ID = os.getenv("REAL_PROJECT_ID", "portfolio-analytics-499108")
TOPIC_NAME = os.getenv("TOPIC_NAME", "b2b-transactions")

DEPARTMENTS = [
    "engineering",
    "marketing",
    "finance",
    "hr",
    "operations",
    "sales",
    "legal",
    "it",
]

PAYMENT_METHODS = ["corporate_card", "ach_transfer", "wire_transfer", "direct_debit"]


# ---------------------------------------------------------------------------
# Load reference data
# ---------------------------------------------------------------------------

def load_csv(path: str) -> list[dict]:
    """Read a CSV file into a list of dicts, one dict per row."""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Transaction generation — normal
# ---------------------------------------------------------------------------

def generate_transaction(company: dict, vendors: list[dict]) -> dict:
    """
    Build one realistic transaction for a given company.

    Amount is drawn from a normal distribution centred on 1% of the company's
    monthly baseline spend — so a mid-market company spending $100k/month will
    typically generate transactions in the $500–$2000 range per event, which
    feels realistic for B2B spend (SaaS subscriptions, ad spend, etc.).
    """
    vendor = random.choice(vendors)

    # Centre the amount on ~1% of monthly baseline, with some spread.
    mean_amount = float(company["baseline_monthly_spend"]) * 0.01
    amount = round(abs(random.gauss(mean_amount, mean_amount * 0.4)), 2)
    amount = max(amount, 10.0)  # floor at $10 — avoids $0.002 transactions
    july_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    random_offset = timedelta(
        days=random.randint(0, 12),      # July 1-13 (up to today)
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    return {
        "transaction_id": str(uuid.uuid4()),
        "company_id": company["company_id"],
        "company_name": company["name"],
        "company_size_tier": company["size_tier"],
        "vendor_id": vendor["vendor_id"],
        "vendor_name": vendor["name"],
        "vendor_category": vendor["category"],
        "vendor_risk_tier": vendor["risk_tier"],
        "amount_usd": amount,
        "currency": "USD",
        "payment_method": random.choice(PAYMENT_METHODS),
        "department": random.choice(DEPARTMENTS),
        "timestamp": (july_start + random_offset).isoformat(),
        "baseline_monthly_spend": float(company["baseline_monthly_spend"]),
        "is_anomaly": False,
        "anomaly_type": None,
    }


# ---------------------------------------------------------------------------
# Transaction generation — anomalies
# ---------------------------------------------------------------------------

def generate_anomaly_transaction(company: dict, vendors: list[dict]) -> dict:
    """
    Deliberately generate a suspicious transaction for anomaly testing.

    Three anomaly types are injected at random:
    - spend_spike: amount is 10–20x the normal mean, simulating a sudden
      large purchase or a compromised card being used for a big transaction.
    - velocity_burst: amount is normal, but the caller (below) fires many of
      these in rapid succession for the same company, simulating a card being
      used repeatedly in a short window.
    - new_vendor_category: picks a category from a fixed "suspicious" list
      that the company would not normally use, simulating an unexpected
      vendor relationship appearing for the first time.
    """
    anomaly_type = random.choice(["spend_spike", "velocity_burst", "new_vendor_category"])
    txn = generate_transaction(company, vendors)
    txn["is_anomaly"] = True
    txn["anomaly_type"] = anomaly_type

    if anomaly_type == "spend_spike":
        # Multiply the normal amount by a large factor
        txn["amount_usd"] = round(txn["amount_usd"] * random.uniform(10, 20), 2)

    elif anomaly_type == "velocity_burst":
        # Amount stays normal — the burst effect comes from the loop in main()
        # firing multiple of these back to back for the same company.
        pass

    elif anomaly_type == "new_vendor_category":
        # Override the vendor with one from an "unusual" category — regardless
        # of what vendors the company normally transacts with.
        unusual_categories = ["travel", "hardware_equipment", "facilities_utilities"]
        unusual_vendors = [v for v in vendors if v["category"] in unusual_categories]
        if unusual_vendors:
            unusual_vendor = random.choice(unusual_vendors)
            txn["vendor_id"] = unusual_vendor["vendor_id"]
            txn["vendor_name"] = unusual_vendor["name"]
            txn["vendor_category"] = unusual_vendor["category"]
            txn["vendor_risk_tier"] = unusual_vendor["risk_tier"]

    return txn


# ---------------------------------------------------------------------------
# Publish to Pub/Sub
# ---------------------------------------------------------------------------

def build_publisher(use_real_pubsub: bool) -> tuple[pubsub_v1.PublisherClient, str]:
    """
    Build a Pub/Sub publisher client and return it alongside the full topic path.

    When use_real_pubsub is False (default), PUBSUB_EMULATOR_HOST must be set
    in the environment (loaded from .env.local above). The google-cloud-pubsub
    library reads that env var automatically and routes traffic to the emulator
    instead of real GCP — no code change required, just the env var.

    When use_real_pubsub is True, we explicitly clear that env var so the
    library ignores the emulator and talks to real GCP.
    """
    if use_real_pubsub:
        # Make sure we don't accidentally still have the emulator host set
        os.environ.pop("PUBSUB_EMULATOR_HOST", None)
        project_id = REAL_PROJECT_ID
        print(f"📡 Publishing to REAL GCP Pub/Sub — project: {project_id}")
    else:
        # Emulator host should already be set from .env.local or the shell
        emulator_host = os.environ.get("PUBSUB_EMULATOR_HOST")
        if not emulator_host:
            raise EnvironmentError(
                "PUBSUB_EMULATOR_HOST is not set. "
                "Either set it in .env.local or run: "
                "export PUBSUB_EMULATOR_HOST=localhost:8085"
            )
        project_id = LOCAL_PROJECT_ID
        print(f"🧪 Publishing to LOCAL Pub/Sub emulator at {emulator_host}")

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, TOPIC_NAME)
    return publisher, topic_path


def publish(publisher: pubsub_v1.PublisherClient, topic_path: str, txn: dict) -> None:
    """Serialize one transaction dict to JSON bytes and publish it."""
    data = json.dumps(txn).encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    # .result() blocks until the broker has acknowledged the message.
    # In production you'd collect futures and resolve them in batch, but for
    # a dev producer this keeps the flow simple and errors visible immediately.
    future.result()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(
    companies: list[dict],
    vendors: list[dict],
    publisher: pubsub_v1.PublisherClient,
    topic_path: str,
    inject_anomalies: bool,
    delay: float,
) -> None:
    """
    Continuously generate and publish transactions until interrupted (Ctrl+C).

    With --inject-anomalies, roughly 1 in 10 transaction events is replaced
    with an anomalous one. Within a velocity_burst anomaly event, we fire 5
    rapid-fire transactions for the same company to simulate a burst pattern.
    """
    count = 0
    print(f"\nPublishing to: {topic_path}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            company = random.choice(companies)

            # Decide whether this event is anomalous (~10% of the time)
            if inject_anomalies and random.random() < 0.10:
                txn = generate_anomaly_transaction(company, vendors)

                if txn["anomaly_type"] == "velocity_burst":
                    # Fire 5 transactions in rapid succession for this company
                    for _ in range(5):
                        burst_txn = generate_anomaly_transaction(company, vendors)
                        burst_txn["anomaly_type"] = "velocity_burst"
                        publish(publisher, topic_path, burst_txn)
                        count += 1
                        print(
                            f"[{count}] ⚡ VELOCITY BURST | "
                            f"{company['company_id']} | "
                            f"${burst_txn['amount_usd']}"
                        )
                    time.sleep(delay)
                    continue

                publish(publisher, topic_path, txn)
                count += 1
                print(
                    f"[{count}] 🚨 ANOMALY ({txn['anomaly_type']}) | "
                    f"{company['company_id']} | "
                    f"{txn['vendor_category']} | "
                    f"${txn['amount_usd']}"
                )

            else:
                txn = generate_transaction(company, vendors)
                publish(publisher, topic_path, txn)
                count += 1
                print(
                    f"[{count}] ✅ normal | "
                    f"{company['company_id']} | "
                    f"{txn['vendor_category']} | "
                    f"${txn['amount_usd']}"
                )

            time.sleep(delay)

    except KeyboardInterrupt:
        print(f"\nStopped. Published {count} messages total.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="B2B transaction producer")
    parser.add_argument(
        "--inject-anomalies",
        action="store_true",
        help="Inject ~10%% anomalous transactions (spend spikes, velocity bursts, new vendor categories)",
    )
    parser.add_argument(
        "--use-real-pubsub",
        action="store_true",
        help="Publish to real GCP Pub/Sub instead of the local emulator",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds between messages (default: 0.5). Set to 0 for maximum speed.",
    )
    args = parser.parse_args()

    companies = load_csv("companies.csv")
    vendors = load_csv("vendors.csv")

    if not companies or not vendors:
        raise RuntimeError(
            "companies.csv or vendors.csv is empty. "
            "Run generate_reference_data.py first."
        )

    publisher, topic_path = build_publisher(use_real_pubsub=args.use_real_pubsub)

    run(
        companies=companies,
        vendors=vendors,
        publisher=publisher,
        topic_path=topic_path,
        inject_anomalies=args.inject_anomalies,
        delay=args.delay,
    )