"""
Generates a realistic synthetic dataset for the Churn Radar source API:
customers, billing events, and usage events, written to a local SQLite
database (source_api/data.db) that main.py serves over HTTP.

Each customer is secretly assigned an internal "trajectory" (healthy /
at_risk / churned) that shapes how their usage and billing events are
generated -- declining login frequency, rising support tickets, a payment
failure, an eventual cancellation, etc. The trajectory itself is NEVER
exposed through the API or written to the customers table -- it exists only
to make the generated behavioral data have real signal, so the downstream
health-score model in dbt has something genuine to detect rather than pure
noise.
"""
import random
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker

fake = Faker()

DB_PATH = Path(__file__).parent / "data.db"

NUM_CUSTOMERS = 400
TODAY = datetime.now(timezone.utc)
EARLIEST_SIGNUP = TODAY - timedelta(days=540)  # ~18 months of history

TRAJECTORY_WEIGHTS = {"healthy": 0.55, "at_risk": 0.30, "churned": 0.15}
PLAN_TIERS = ["Starter", "Growth", "Enterprise"]
PLAN_MRR = {"Starter": 99, "Growth": 499, "Enterprise": 1999}
INDUSTRIES = [
    "SaaS", "E-commerce", "Fintech", "Healthcare", "Manufacturing",
    "Media", "Logistics", "Education", "Real Estate", "Professional Services",
]
EMPLOYEE_BANDS = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
FEATURES = [
    "dashboard", "reporting", "integrations", "automation_rules",
    "team_permissions", "api_access", "custom_fields", "bulk_export",
]


def weighted_trajectory():
    return random.choices(
        list(TRAJECTORY_WEIGHTS.keys()),
        weights=list(TRAJECTORY_WEIGHTS.values()),
    )[0]


def random_datetime_between(start, end):
    if end <= start:
        return start
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def build_customers():
    customers = []
    for _ in range(NUM_CUSTOMERS):
        trajectory = weighted_trajectory()
        signup_date = random_datetime_between(EARLIEST_SIGNUP, TODAY - timedelta(days=14))
        plan_tier = random.choices(PLAN_TIERS, weights=[0.5, 0.35, 0.15])[0]

        customer = {
            "customer_id": str(uuid.uuid4()),
            "company_name": fake.company(),
            "industry": random.choice(INDUSTRIES),
            "plan_tier": plan_tier,
            "employee_count_band": random.choice(EMPLOYEE_BANDS),
            "country": fake.country(),
            "signup_date": signup_date.isoformat(),
            "mrr": PLAN_MRR[plan_tier],
            "status": "active",
            "updated_at": TODAY.isoformat(),
            "_trajectory": trajectory,  # stripped before insert -- internal only
        }
        customers.append(customer)
    return customers


def build_billing_events(customer):
    events = []
    signup_date = datetime.fromisoformat(customer["signup_date"])
    trajectory = customer["_trajectory"]
    plan_tier = customer["plan_tier"]
    mrr = PLAN_MRR[plan_tier]

    events.append({
        "event_id": str(uuid.uuid4()),
        "customer_id": customer["customer_id"],
        "event_timestamp": signup_date.isoformat(),
        "event_type": "subscription_started",
        "mrr_before": 0,
        "mrr_after": mrr,
        "plan_tier": plan_tier,
        "created_at": signup_date.isoformat(),
    })

    if trajectory == "healthy" and random.random() < 0.3:
        upgrade_date = random_datetime_between(signup_date + timedelta(days=30), TODAY)
        new_tier = PLAN_TIERS[min(PLAN_TIERS.index(plan_tier) + 1, len(PLAN_TIERS) - 1)]
        new_mrr = PLAN_MRR[new_tier]
        if new_tier != plan_tier:
            events.append({
                "event_id": str(uuid.uuid4()),
                "customer_id": customer["customer_id"],
                "event_timestamp": upgrade_date.isoformat(),
                "event_type": "plan_upgraded",
                "mrr_before": mrr,
                "mrr_after": new_mrr,
                "plan_tier": new_tier,
                "created_at": upgrade_date.isoformat(),
            })
            mrr = new_mrr
            customer["mrr"] = new_mrr
            customer["plan_tier"] = new_tier

    cancel_date = None

    if trajectory in ("at_risk", "churned") and random.random() < 0.6:
        failure_date = random_datetime_between(TODAY - timedelta(days=90), TODAY - timedelta(days=10))
        events.append({
            "event_id": str(uuid.uuid4()),
            "customer_id": customer["customer_id"],
            "event_timestamp": failure_date.isoformat(),
            "event_type": "payment_failed",
            "mrr_before": mrr,
            "mrr_after": mrr,
            "plan_tier": customer["plan_tier"],
            "created_at": failure_date.isoformat(),
        })

    if trajectory == "churned":
        cancel_date = random_datetime_between(
            max(signup_date + timedelta(days=45), TODAY - timedelta(days=120)),
            TODAY - timedelta(days=3),
        )
        events.append({
            "event_id": str(uuid.uuid4()),
            "customer_id": customer["customer_id"],
            "event_timestamp": cancel_date.isoformat(),
            "event_type": "subscription_canceled",
            "mrr_before": mrr,
            "mrr_after": 0,
            "plan_tier": customer["plan_tier"],
            "created_at": cancel_date.isoformat(),
        })
        customer["status"] = "canceled"
        customer["mrr"] = 0

    return events, cancel_date


def build_usage_events(customer, cancel_date):
    events = []
    signup_date = datetime.fromisoformat(customer["signup_date"])
    trajectory = customer["_trajectory"]
    activity_end = cancel_date or TODAY

    active_days = max((activity_end - signup_date).days, 1)

    if trajectory == "healthy":
        logins_per_week = random.uniform(3, 6)
        ticket_rate = 0.02
    elif trajectory == "at_risk":
        logins_per_week = random.uniform(2, 4)
        ticket_rate = 0.08
    else:  # churned
        logins_per_week = random.uniform(2, 5)
        ticket_rate = 0.10

    total_logins = int((active_days / 7) * logins_per_week)

    for _ in range(total_logins):
        if trajectory in ("at_risk", "churned"):
            # bias timestamps toward the earlier part of the customer's
            # lifetime, so the last 30-45 days show a visible drop-off --
            # the actual behavioral signal the health score should detect
            quiet_start = activity_end - timedelta(days=random.choice([30, 45]))
            window_end = max(min(quiet_start, activity_end), signup_date + timedelta(days=1))
            ts = random_datetime_between(signup_date, window_end)
        else:
            ts = random_datetime_between(signup_date, activity_end)

        events.append({
            "event_id": str(uuid.uuid4()),
            "customer_id": customer["customer_id"],
            "event_timestamp": ts.isoformat(),
            "event_type": "login",
            "feature_name": None,
            "session_duration_seconds": random.randint(60, 2400),
            "user_email": fake.company_email(),
            "created_at": ts.isoformat(),
        })

        if random.random() < 0.4:
            events.append({
                "event_id": str(uuid.uuid4()),
                "customer_id": customer["customer_id"],
                "event_timestamp": ts.isoformat(),
                "event_type": "feature_used",
                "feature_name": random.choice(FEATURES),
                "session_duration_seconds": None,
                "user_email": fake.company_email(),
                "created_at": ts.isoformat(),
            })

    num_tickets = int(total_logins * ticket_rate)
    for _ in range(num_tickets):
        opened_at = random_datetime_between(signup_date, activity_end)
        events.append({
            "event_id": str(uuid.uuid4()),
            "customer_id": customer["customer_id"],
            "event_timestamp": opened_at.isoformat(),
            "event_type": "support_ticket_opened",
            "feature_name": None,
            "session_duration_seconds": None,
            "user_email": fake.company_email(),
            "created_at": opened_at.isoformat(),
        })
        if random.random() < 0.7:
            resolved_at = opened_at + timedelta(hours=random.randint(2, 72))
            events.append({
                "event_id": str(uuid.uuid4()),
                "customer_id": customer["customer_id"],
                "event_timestamp": resolved_at.isoformat(),
                "event_type": "support_ticket_resolved",
                "feature_name": None,
                "session_duration_seconds": None,
                "user_email": fake.company_email(),
                "created_at": resolved_at.isoformat(),
            })

    return events


def build_database():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            company_name TEXT,
            industry TEXT,
            plan_tier TEXT,
            employee_count_band TEXT,
            country TEXT,
            signup_date TEXT,
            mrr REAL,
            status TEXT,
            updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE billing_events (
            event_id TEXT PRIMARY KEY,
            customer_id TEXT,
            event_timestamp TEXT,
            event_type TEXT,
            mrr_before REAL,
            mrr_after REAL,
            plan_tier TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE usage_events (
            event_id TEXT PRIMARY KEY,
            customer_id TEXT,
            event_timestamp TEXT,
            event_type TEXT,
            feature_name TEXT,
            session_duration_seconds INTEGER,
            user_email TEXT,
            created_at TEXT
        )
    """)

    customers = build_customers()

    for customer in customers:
        billing_events, cancel_date = build_billing_events(customer)
        usage_events = build_usage_events(customer, cancel_date)

        customer_row = {k: v for k, v in customer.items() if not k.startswith("_")}
        cur.execute(
            """INSERT INTO customers VALUES (:customer_id, :company_name, :industry,
               :plan_tier, :employee_count_band, :country, :signup_date, :mrr,
               :status, :updated_at)""",
            customer_row,
        )

        cur.executemany(
            """INSERT INTO billing_events VALUES (:event_id, :customer_id,
               :event_timestamp, :event_type, :mrr_before, :mrr_after,
               :plan_tier, :created_at)""",
            billing_events,
        )
        cur.executemany(
            """INSERT INTO usage_events VALUES (:event_id, :customer_id,
               :event_timestamp, :event_type, :feature_name,
               :session_duration_seconds, :user_email, :created_at)""",
            usage_events,
        )

    conn.commit()
    conn.close()
    print(f"Generated {len(customers)} customers into {DB_PATH}")


if __name__ == "__main__":
    build_database()
