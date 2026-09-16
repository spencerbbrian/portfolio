"""
Signal - Synthetic telecom subscriber data generator.

Generates six related CSV files that model a telecom subscriber lifecycle:
subscribers, plans, subscription_history, devices, usage_events, support_tickets,
and ticket_status_history.

Run with: python generate_signal_data.py
Output lands in ./output/*.csv
"""

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# Seed everything so the dataset is reproducible - if you or someone reviewing
# your project re-runs this script, they get the exact same data, which matters
# for debugging ("did my dbt model break, or did my data change?").
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# ---------------------------------------------------------------------------
# Configuration - tune these to make the dataset bigger/smaller
# ---------------------------------------------------------------------------
NUM_SUBSCRIBERS = 5000
NUM_TICKETS = 2500
SIMULATION_START = datetime(2023, 1, 1)   # earliest a subscriber could sign up
SIMULATION_END = datetime(2026, 9, 1)     # "today" in the simulated world
OUTPUT_DIR = "output"

# ---------------------------------------------------------------------------
# 1. PLANS - a fixed reference list, not randomly generated.
#    Real telecoms have a small, deliberate set of plans, so this is hand-authored.
#    "weight" controls how likely a subscriber is to be on that plan - it's what
#    makes the data realistic instead of uniformly spread across all 8 options.
# ---------------------------------------------------------------------------
PLANS = [
    # plan_id, plan_name,          plan_type,  data_gb, voice_min, sms,  monthly_price, weight
    (1, "Basic 2GB",        "prepaid",  2,    100,  50,   9.99,  0.10),
    (2, "Basic 5GB",        "prepaid",  5,    200,  100,  14.99, 0.20),
    (3, "Standard 10GB",    "postpaid", 10,   500,  250,  24.99, 0.25),
    (4, "Standard 20GB",    "postpaid", 20,   750,  500,  34.99, 0.18),
    (5, "Unlimited Plus",   "postpaid", 9999, 9999, 9999, 49.99, 0.15),
    (6, "Family Share 50GB","postpaid", 50,   1500, 1000, 59.99, 0.07),
    (7, "Business Pro",     "postpaid", 100,  9999, 9999, 79.99, 0.03),
    (8, "IoT Data Only",    "prepaid",  1,    0,    0,    4.99,  0.02),
]
PLAN_IDS = [p[0] for p in PLANS]
PLAN_WEIGHTS = [p[7] for p in PLANS]

DEVICE_BRANDS = [
    ("Apple",   ["iPhone 13", "iPhone 14", "iPhone 15", "iPhone 16"], 0.40),
    ("Samsung", ["Galaxy S22", "Galaxy S23", "Galaxy S24", "Galaxy A54"], 0.35),
    ("Google",  ["Pixel 7", "Pixel 8", "Pixel 9"], 0.10),
    ("Xiaomi",  ["Redmi Note 12", "Redmi Note 13"], 0.08),
    ("Other",   ["Generic Android Phone"], 0.07),
]
BRAND_WEIGHTS = [b[2] for b in DEVICE_BRANDS]

TICKET_CATEGORIES = ["billing", "technical", "plan_change", "device_issue", "network"]
TICKET_PRIORITIES = ["low", "medium", "high", "urgent"]
STATUS_SEQUENCE = ["open", "in_progress", "resolved"]  # a ticket moves through these in order


def random_date_between(start: datetime, end: datetime) -> datetime:
    """Pick a random datetime between two datetimes - used everywhere below
    instead of Faker's own date functions so we can control the exact window."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def build_plans_df() -> pd.DataFrame:
    """Just reshapes the PLANS constant above into a DataFrame - this becomes plans.csv."""
    return pd.DataFrame(
        PLANS,
        columns=["plan_id", "plan_name", "plan_type", "data_allowance_gb",
                 "voice_minutes", "sms_allowance", "monthly_price", "_weight"],
    ).drop(columns=["_weight"])


def build_subscribers_and_subscription_history():
    """
    Builds two related tables together because they share the same loop:
    - subscribers: one row per subscriber
    - subscription_history: one or more rows per subscriber, tracking every
      plan they've ever been on (this is the SCD2 source data)
    """
    subscribers = []
    subscription_history = []

    for i in range(1, NUM_SUBSCRIBERS + 1):
        subscriber_id = f"SUB-{i:06d}"
        signup_date = random_date_between(SIMULATION_START, SIMULATION_END - timedelta(days=30))

        # 15% of subscribers have churned (cancelled); the rest are still active.
        is_churned = random.random() < 0.15
        churn_date = None
        if is_churned:
            # churn happens sometime after signup, before "today"
            earliest_churn = signup_date + timedelta(days=30)
            if earliest_churn < SIMULATION_END:
                churn_date = random_date_between(earliest_churn, SIMULATION_END)
            else:
                is_churned = False  # not enough time between signup and "today" to have churned

        subscribers.append({
            "subscriber_id": subscriber_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
            "phone_number": fake.phone_number(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat(),
            "signup_date": signup_date.date().isoformat(),
            "status": "churned" if is_churned else "active",
            "churn_date": churn_date.date().isoformat() if churn_date else None,
        })

        # --- Build this subscriber's plan history ---
        # Most subscribers (70%) never switch plans - one row, no end_date.
        # The other 30% switch 1-2 times, which is what gives dim_subscriber's
        # SCD2 something real to track.
        num_plan_changes = 0 if random.random() < 0.70 else random.choice([1, 2])
        segment_start = signup_date
        segment_end_cap = churn_date if churn_date else SIMULATION_END

        for change_num in range(num_plan_changes + 1):
            plan_id = random.choices(PLAN_IDS, weights=PLAN_WEIGHTS, k=1)[0]
            remaining_days = (segment_end_cap - segment_start).days
            # Only attempt a switch if this isn't the final planned segment AND
            # there are at least 30 days of runway left to place that switch in -
            # otherwise just let this plan ride out as the final segment.
            is_last_segment = (change_num == num_plan_changes) or (remaining_days < 30)

            if is_last_segment:
                seg_end = None  # still on this plan (or churned - segment just stops)
            else:
                seg_end = segment_start + timedelta(days=random.randint(30, remaining_days))

            subscription_history.append({
                "subscriber_id": subscriber_id,
                "plan_id": plan_id,
                "start_date": segment_start.date().isoformat(),
                "end_date": seg_end.date().isoformat() if seg_end else None,
            })

            if seg_end:
                segment_start = seg_end
            else:
                break  # no more segments once we've hit the final one

    return pd.DataFrame(subscribers), pd.DataFrame(subscription_history)


def build_devices(subscriber_ids: list) -> pd.DataFrame:
    """Most subscribers have exactly one device; some have two (e.g. a phone + a tablet)."""
    devices = []
    device_counter = 1
    for subscriber_id in subscriber_ids:
        num_devices = 1 if random.random() < 0.85 else 2
        for _ in range(num_devices):
            brand, models, _ = random.choices(DEVICE_BRANDS, weights=BRAND_WEIGHTS, k=1)[0]
            devices.append({
                "device_id": f"DEV-{device_counter:06d}",
                "subscriber_id": subscriber_id,
                "brand": brand,
                "model": random.choice(models),
                "imei": fake.numerify("##############"),
                "device_type": "tablet" if "tablet" in " ".join(models).lower() else "smartphone",
            })
            device_counter += 1
    return pd.DataFrame(devices)


def build_usage_events(subscription_history_df: pd.DataFrame, devices_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each subscriber, generate a handful of usage events (data/call/sms) that fall
    within a period they were actually subscribed to a specific plan - so plan_id here
    is always the plan that was ACTUALLY ACTIVE at that moment, not just their current one.
    """
    events = []
    event_counter = 1
    devices_by_subscriber = devices_df.groupby("subscriber_id")["device_id"].apply(list).to_dict()

    for _, row in subscription_history_df.iterrows():
        subscriber_id = row["subscriber_id"]
        plan_id = row["plan_id"]
        seg_start = datetime.fromisoformat(row["start_date"])
        seg_end = datetime.fromisoformat(row["end_date"]) if pd.notna(row["end_date"]) else SIMULATION_END

        device_ids = devices_by_subscriber.get(subscriber_id, [])
        if not device_ids:
            continue

        # ~15-40 usage events per subscriber per plan segment
        num_events = random.randint(15, 40)
        for _ in range(num_events):
            event_time = random_date_between(seg_start, seg_end)
            event_type = random.choices(["data", "call", "sms"], weights=[0.6, 0.25, 0.15], k=1)[0]

            events.append({
                "usage_event_id": f"EVT-{event_counter:08d}",
                "subscriber_id": subscriber_id,
                "device_id": random.choice(device_ids),
                "plan_id": plan_id,
                "event_type": event_type,
                "event_timestamp": event_time.isoformat(),
                "data_used_mb": round(random.uniform(1, 2000), 2) if event_type == "data" else None,
                "call_duration_seconds": random.randint(10, 3600) if event_type == "call" else None,
                "sms_count": random.randint(1, 5) if event_type == "sms" else None,
            })
            event_counter += 1

    return pd.DataFrame(events)


def build_support_tickets_and_status_history(subscriber_ids: list):
    """
    Same pairing pattern as subscribers/subscription_history:
    - support_tickets: one row per ticket, with its final/current status
    - ticket_status_history: multiple rows per ticket, one per status change over time
    """
    tickets = []
    status_history = []

    for i in range(1, NUM_TICKETS + 1):
        ticket_id = f"TIX-{i:06d}"
        subscriber_id = random.choice(subscriber_ids)
        created_at = random_date_between(SIMULATION_START, SIMULATION_END)

        # 80% of tickets reach "resolved", 20% are still stuck earlier (open/in_progress)
        reaches_resolved = random.random() < 0.80
        stages = STATUS_SEQUENCE if reaches_resolved else STATUS_SEQUENCE[: random.randint(1, 2)]

        current_time = created_at
        for stage in stages:
            status_history.append({
                "ticket_id": ticket_id,
                "status": stage,
                "changed_at": current_time.isoformat(),
            })
            # each stage lasts a few hours to a few days before the next change
            current_time = current_time + timedelta(hours=random.randint(2, 72))

        tickets.append({
            "ticket_id": ticket_id,
            "subscriber_id": subscriber_id,
            "created_at": created_at.isoformat(),
            "category": random.choice(TICKET_CATEGORIES),
            "priority": random.choice(TICKET_PRIORITIES),
            "current_status": stages[-1],
            "resolved_at": current_time.isoformat() if stages[-1] == "resolved" else None,
        })

    return pd.DataFrame(tickets), pd.DataFrame(status_history)


def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Generating plans...")
    plans_df = build_plans_df()

    print(f"Generating {NUM_SUBSCRIBERS} subscribers and their subscription history...")
    subscribers_df, subscription_history_df = build_subscribers_and_subscription_history()

    print("Generating devices...")
    devices_df = build_devices(subscribers_df["subscriber_id"].tolist())

    print("Generating usage events (this is the slow one)...")
    usage_events_df = build_usage_events(subscription_history_df, devices_df)

    print(f"Generating {NUM_TICKETS} support tickets and their status history...")
    tickets_df, ticket_status_history_df = build_support_tickets_and_status_history(
        subscribers_df["subscriber_id"].tolist()
    )

    # Write everything out as CSVs - these are the "raw" files step 5 will load into Snowflake.
    plans_df.to_csv(f"{OUTPUT_DIR}/plans.csv", index=False)
    subscribers_df.to_csv(f"{OUTPUT_DIR}/subscribers.csv", index=False)
    subscription_history_df.to_csv(f"{OUTPUT_DIR}/subscription_history.csv", index=False)
    devices_df.to_csv(f"{OUTPUT_DIR}/devices.csv", index=False)
    usage_events_df.to_csv(f"{OUTPUT_DIR}/usage_events.csv", index=False)
    tickets_df.to_csv(f"{OUTPUT_DIR}/support_tickets.csv", index=False)
    ticket_status_history_df.to_csv(f"{OUTPUT_DIR}/ticket_status_history.csv", index=False)

    print("\nDone. Row counts:")
    print(f"  plans:                  {len(plans_df):>8,}")
    print(f"  subscribers:            {len(subscribers_df):>8,}")
    print(f"  subscription_history:   {len(subscription_history_df):>8,}")
    print(f"  devices:                {len(devices_df):>8,}")
    print(f"  usage_events:           {len(usage_events_df):>8,}")
    print(f"  support_tickets:        {len(tickets_df):>8,}")
    print(f"  ticket_status_history:  {len(ticket_status_history_df):>8,}")


if __name__ == "__main__":
    main()