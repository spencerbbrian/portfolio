import os
import random
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from schemas import ALLOWED_EVENT_TYPES, ALLOWED_ORDER_STATUSES, COLLECTION_PRODUCTS, COLLECTION_USERS

load_dotenv()
fake = Faker()

DB_NAME = os.getenv("MONGO_DB_NAME")

EVENT_TYPES = (
    "page_view",
    "add_to_cart",
    "checkout_started",
    "purchase",
    "remove_from_cart"
)
WEIGHTS = (60, 20, 10, 8, 2)

assert set(EVENT_TYPES) == set(ALLOWED_EVENT_TYPES), "EVENT_TYPES and ALLOWED_EVENT_TYPES must match"
assert sum(WEIGHTS) == 100, "Weights must sum to 100"


class ReferenceDataPool:
    """ Gets real user-ids and product-ids from the database to use in event generation. """

    def __init__(self, user_ids: list[str], product_ids: list[str]):
        if not user_ids:
            raise ValueError("No user_ids loaded yet. Run the mongo/seed.py")
        if not product_ids:
            raise ValueError("No product_ids loaded. Run mongo/seed.py")
        self.user_ids = user_ids
        self.product_ids = product_ids

    def random_user_id(self) -> str:
        return random.choice(self.user_ids)

    def random_product_id(self) -> str:
        return random.choice(self.product_ids)


def load_reference_pool(mongo_uri: Optional[str] = None) -> ReferenceDataPool:
    """Connect to MongoDB and pulls in all user and product ids"""
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("Error: No MONGO_URI in the env file")
        sys.exit(1)

    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    try:
        client.admin.command("ping")
    except ConnectionFailure as exc:
        print(f" Error: could not connect to MongoDB - {exc}")
        sys.exit(1)

    db = client[DB_NAME]

    user_ids = [doc["user_id"] for doc in db[COLLECTION_USERS].find({}, {"user_id": 1})]
    products_ids = [doc["sku"] for doc in db[COLLECTION_PRODUCTS].find({}, {"sku": 1})]

    client.close()

    return ReferenceDataPool(user_ids=user_ids, product_ids=products_ids)


# Event generaton 
def pick_weighted_event_type() -> str:
    return random.choices(EVENT_TYPES, weights=WEIGHTS, k=1)[0]


def _build_metadata() -> dict:
    """Fake metadata enriched further by the Kafka consumer (geo, device)."""
    return {
        "ip": fake.ipv4_public(),
        "user_agent": fake.user_agent(),
    }


def _build_shipping_address() -> dict:
    return {
        "line1": fake.street_address(),
        "line2": None,
        "city": fake.city(),
        "postal_code": fake.postcode(),
        "country": fake.country_code(),
    }


def generate_event(event_type: str, pool: ReferenceDataPool, session_id: Optional[str] = None) -> dict:
    """Build a single event that matches schema of events document."""
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"Unknown event_type '{event_type}'. Must be one of {ALLOWED_EVENT_TYPES}")
    event = {
        "type": event_type,
        "user_id": pool.random_user_id(),
        "session_id": session_id or f"sess_{uuid.uuid4().hex[:12]}",
        "product_id": pool.random_product_id(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": _build_metadata(),
    }
    return event


def generate_order(purchase_event: dict) -> dict:
    """
    Builds an order document from a purchase event.

    Takes the purchase event as input so the order shares the same
    user_id, product_id, and session_id — keeping them consistent
    rather than generating new random IDs that don't match the event.

    The order matches schemas.OrderDocument: line items and shipping
    address are embedded as snapshots (prices/addresses can change later,
    but this order is a receipt — it captures state at purchase time).
    """
    quantity = random.randint(1, 4)
    unit_price = round(random.uniform(9.99, 249.99), 2)
    subtotal = round(unit_price * quantity, 2)
    tax = round(subtotal * 0.20, 2)
    shipping = round(random.uniform(0, 15.99), 2)
    total = round(subtotal + tax + shipping, 2)

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    order_id = f"ORD-{date_str}-{uuid.uuid4().hex[:6].upper()}"

    return {
        "order_id": order_id,
        "user_id": purchase_event["user_id"],
        "session_id": purchase_event["session_id"],
        "items": [
            {
                # name_snapshot: using SKU as stand-in — consumer could enrich
                # this by looking up the product name from the catalogue later.
                "product_id": purchase_event["product_id"],
                "name_snapshot": purchase_event["product_id"],
                "unit_price": unit_price,
                "quantity": quantity,
            }
        ],
        "totals": {
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "total": total,
        },
        "status": "pending",
        "shipping_address": _build_shipping_address(),
        "created_at": purchase_event["timestamp"],
    }


def generate_random_event(pool: ReferenceDataPool, session_id: Optional[str] = None) -> dict:
    event_type = pick_weighted_event_type()
    return generate_event(event_type, pool, session_id=session_id)


# Manual Test
if __name__ == "__main__":
    pool = load_reference_pool()
    print(f"Loaded {len(pool.user_ids)} users and {len(pool.product_ids)} products.\n")

    print("Sample events:")
    for _ in range(5):
        event = generate_random_event(pool)
        print(event)

    print("\nSample purchase + order pair:")
    purchase = generate_event("purchase", pool)
    order = generate_order(purchase)
    print("  event:", purchase)
    print("  order:", order)
    print("  IDs match:", purchase["user_id"] == order["user_id"] and purchase["session_id"] == order["session_id"])

    print("\nWeighting check (1000 samples):")
    from collections import Counter
    sample = [pick_weighted_event_type() for _ in range(1000)]
    counts = Counter(sample)
    for event_type in EVENT_TYPES:
        print(f"  {event_type}: {counts[event_type] / 10:.1f}%")