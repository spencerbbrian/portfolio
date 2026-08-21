"""
consumer/kafka_consumer.py

Subscribes to the 'events' and 'orders' Kafka topics, and for each message:
  1. Deserialises JSON
  2. Validates required fields and allowed values
  3. Enriches with geo (country/city from IP) and device type (from user-agent)
  4. Writes to MongoDB Atlas (events → events collection, orders → orders collection)
  5. On validation failure, routes to the 'dlq' topic instead of MongoDB

Run from project root:
    python -m consumer.kafka_consumer

Design notes:
  - validate() and enrich() are pure functions — no side effects, easy to test
  - DLQ (dead letter queue) means bad messages are never silently dropped;
    you can inspect and replay them later
  - upsert on order_id prevents duplicates if the consumer restarts and
    replays already-processed messages (idempotent writes)
  - geo enrichment is stubbed with Faker for simulation — in production
    replace _geo_lookup() with MaxMind geoip2 local DB (no rate limits,
    no HTTP calls, works offline)
"""

import json
import os
import random
import sys
from datetime import datetime, timezone
from typing import Optional

from confluent_kafka import Consumer, KafkaError, Producer
from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from schemas import (
    ALLOWED_EVENT_TYPES,
    ALLOWED_ORDER_STATUSES,
    COLLECTION_EVENTS,
    COLLECTION_ORDERS,
)

load_dotenv()
fake = Faker()

TOPIC_EVENTS = "events"
TOPIC_ORDERS = "orders"
TOPIC_DLQ    = "dlq"
DB_NAME      = os.getenv("MONGO_DB_NAME", "ecommerce_pipeline")

# ---------------------------------------------------------------------------
# Kafka config
# ---------------------------------------------------------------------------

def build_consumer_config() -> dict:
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    api_key           = os.getenv("KAFKA_API_KEY")
    api_secret        = os.getenv("KAFKA_API_SECRET")

    missing = [
        name for name, value in [
            ("KAFKA_BOOTSTRAP_SERVERS", bootstrap_servers),
            ("KAFKA_API_KEY",           api_key),
            ("KAFKA_API_SECRET",        api_secret),
        ] if not value
    ]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}")
        sys.exit(1)

    return {
        "bootstrap.servers":  bootstrap_servers,
        "security.protocol":  "SASL_SSL",
        "sasl.mechanisms":    "PLAIN",
        "sasl.username":      api_key,
        "sasl.password":      api_secret,
        "group.id":           "ecommerce-consumer-group",
        # earliest: on first run, read all messages from the start of the topic.
        # If the consumer restarts, it resumes from its last committed offset instead.
        "auto.offset.reset":  "earliest",
        # disable auto-commit so we control exactly when offsets are committed
        # (after successful MongoDB write, not just after poll)
        "enable.auto.commit": False,
        "client.id":          "ecommerce-consumer",
    }


def build_producer_config() -> dict:
    """Small producer used only to write failed messages to the DLQ topic."""
    return {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms":   "PLAIN",
        "sasl.username":     os.getenv("KAFKA_API_KEY"),
        "sasl.password":     os.getenv("KAFKA_API_SECRET"),
        "client.id":         "ecommerce-dlq-producer",
    }


# ---------------------------------------------------------------------------
# MongoDB connection
# ---------------------------------------------------------------------------

def get_db():
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("ERROR: MONGO_URI not found in environment.")
        sys.exit(1)

    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    try:
        client.admin.command("ping")
    except ConnectionFailure as exc:
        print(f"ERROR: could not connect to MongoDB — {exc}")
        sys.exit(1)

    return client[DB_NAME]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_event(doc: dict) -> Optional[str]:
    """
    Returns None if the event is valid, or an error string if not.
    Checked before enrichment and before writing to MongoDB.
    """
    required = ["type", "user_id", "session_id", "timestamp"]
    for field in required:
        if not doc.get(field):
            return f"missing required field: '{field}'"

    if doc["type"] not in ALLOWED_EVENT_TYPES:
        return f"invalid event type: '{doc['type']}'"

    try:
        datetime.fromisoformat(doc["timestamp"])
    except ValueError:
        return f"unparseable timestamp: '{doc['timestamp']}'"

    return None


def validate_order(doc: dict) -> Optional[str]:
    """Returns None if valid, error string if not."""
    required = ["order_id", "user_id", "items", "totals", "status", "created_at"]
    for field in required:
        if not doc.get(field):
            return f"missing required field: '{field}'"

    if doc["status"] not in ALLOWED_ORDER_STATUSES:
        return f"invalid order status: '{doc['status']}'"

    if not isinstance(doc["items"], list) or len(doc["items"]) == 0:
        return "items must be a non-empty list"

    if doc["totals"].get("total", -1) < 0:
        return "order total must be non-negative"

    return None


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------

def _geo_lookup(ip: str) -> dict:
    """
    Stubbed for simulation — returns Faker-generated geo data.
    In production replace with MaxMind geoip2 local DB:
        import geoip2.database
        reader = geoip2.database.Reader('GeoLite2-City.mmdb')
        response = reader.city(ip)
    No rate limits, no HTTP calls, works offline.
    """
    return {
        "country":      fake.country(),
        "country_code": fake.country_code(),
        "city":         fake.city(),
    }


def _parse_device(user_agent: str) -> dict:
    """
    Parses a User-Agent string into device_type and browser.
    Uses simple string matching — avoids the user-agents library dependency
    while still being accurate enough for analytics segmentation.
    """
    ua = user_agent.lower()

    if any(t in ua for t in ["iphone", "android", "mobile", "fxios", "crios"]):
        device_type = "mobile"
    elif any(t in ua for t in ["ipad", "tablet"]):
        device_type = "tablet"
    else:
        device_type = "desktop"

    if "firefox" in ua or "fxios" in ua:
        browser = "Firefox"
    elif "edg" in ua:
        browser = "Edge"
    elif "chrome" in ua or "crios" in ua:
        browser = "Chrome"
    elif "safari" in ua:
        browser = "Safari"
    elif "opera" in ua or "opr" in ua:
        browser = "Opera"
    elif "msie" in ua or "trident" in ua:
        browser = "IE"
    else:
        browser = "Other"

    return {"device_type": device_type, "browser": browser}


def enrich_event(doc: dict) -> dict:
    """
    Adds geo and device fields to event metadata.
    Always returns the doc even if enrichment partially fails.
    """
    metadata = doc.setdefault("metadata", {})
    ip = metadata.get("ip", "")
    ua = metadata.get("user_agent", "")

    if ip:
        geo = _geo_lookup(ip)
        metadata.update(geo)

    if ua:
        device = _parse_device(ua)
        metadata.update(device)

    return doc


# ---------------------------------------------------------------------------
# MongoDB writes
# ---------------------------------------------------------------------------

def write_event(db, doc: dict) -> None:
    db[COLLECTION_EVENTS].insert_one(doc)


def write_order(db, doc: dict) -> None:
    # upsert on order_id — safe to replay without creating duplicates
    db[COLLECTION_ORDERS].update_one(
        {"order_id": doc["order_id"]},
        {"$set": doc},
        upsert=True,
    )


def send_to_dlq(dlq_producer: Producer, original_msg, reason: str) -> None:
    """Forwards a failed message to the DLQ topic with the failure reason attached."""
    try:
        payload = {
            "original_topic": original_msg.topic(),
            "original_value": original_msg.value().decode("utf-8"),
            "reason": reason,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        dlq_producer.produce(
            topic=TOPIC_DLQ,
            value=json.dumps(payload),
        )
        dlq_producer.poll(0)
    except Exception as exc:
        print(f"  WARNING: could not write to DLQ — {exc}")


# ---------------------------------------------------------------------------
# Main consume loop
# ---------------------------------------------------------------------------

def run_consumer() -> None:
    db           = get_db()
    consumer     = Consumer(build_consumer_config())
    dlq_producer = Producer(build_producer_config())

    consumer.subscribe([TOPIC_EVENTS, TOPIC_ORDERS])
    print(f"Subscribed to: {TOPIC_EVENTS}, {TOPIC_ORDERS}")
    print("Waiting for messages... (Ctrl+C to stop)\n")

    events_written = 0
    orders_written = 0
    dlq_count      = 0

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            # poll() returns None when no message arrived within the timeout —
            # this is normal, not an error. Just loop and poll again.
            if msg is None:
                continue

            if msg.error():
                # PARTITION_EOF is informational (reached end of partition),
                # not a real error — safe to ignore.
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"  consumer error: {msg.error()}")
                continue

            # --- deserialise ---
            try:
                doc = json.loads(msg.value().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                print(f"  deserialisation error: {exc} — sending to DLQ")
                send_to_dlq(dlq_producer, msg, reason=str(exc))
                dlq_count += 1
                consumer.commit(message=msg)
                continue

            topic = msg.topic()

            # --- validate ---
            if topic == TOPIC_EVENTS:
                error = validate_event(doc)
            elif topic == TOPIC_ORDERS:
                error = validate_order(doc)
            else:
                error = f"unexpected topic: {topic}"

            if error:
                print(f"  validation failed ({topic}): {error} — sending to DLQ")
                send_to_dlq(dlq_producer, msg, reason=error)
                dlq_count += 1
                consumer.commit(message=msg)
                continue

            # --- enrich (events only — orders don't have metadata) ---
            if topic == TOPIC_EVENTS:
                doc = enrich_event(doc)

            # --- write to MongoDB ---
            try:
                if topic == TOPIC_EVENTS:
                    write_event(db, doc)
                    events_written += 1
                elif topic == TOPIC_ORDERS:
                    write_order(db, doc)
                    orders_written += 1
            except Exception as exc:
                print(f"  MongoDB write error: {exc} — sending to DLQ")
                send_to_dlq(dlq_producer, msg, reason=str(exc))
                dlq_count += 1
                consumer.commit(message=msg)
                continue

            # commit offset only after successful MongoDB write
            consumer.commit(message=msg)

            if (events_written + orders_written) % 50 == 0:
                print(f"  events={events_written}  orders={orders_written}  dlq={dlq_count}")

    except KeyboardInterrupt:
        print("\nStopping consumer...")
    finally:
        consumer.close()
        dlq_producer.flush(timeout=5)
        print(f"\nDone. events={events_written}  orders={orders_written}  dlq={dlq_count}")


if __name__ == "__main__":
    run_consumer()