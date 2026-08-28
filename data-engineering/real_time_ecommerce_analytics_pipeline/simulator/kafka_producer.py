"""
simulator/kafka_producer.py

This calls repeatedly the event-generator to produce events and send them to Kafka connected to Confluence.
"""

import argparse
import json
import os
import signal
import sys
import time
from typing import Optional

from confluent_kafka import KafkaError, Producer
from dotenv import load_dotenv

from simulator.event_generator import generate_random_event, load_reference_pool, generate_order

load_dotenv()

TOPIC_EVENTS = "events"
TOPIC_ORDERS = "orders"  


def build_producer_config() -> dict:
    """
    Builds the Kafka producer config for Confluent Cloud.

    Confluent Cloud requires SASL_SSL with PLAIN auth using your API key/secret
    as username/password — this is different from a local/unauthenticated
    Kafka setup, so don't drop these security.protocol/sasl.* lines.
    """
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    api_key = os.getenv("KAFKA_API_KEY")
    api_secret = os.getenv("KAFKA_API_SECRET")

    missing = [
        name
        for name, value in [
            ("KAFKA_BOOTSTRAP_SERVERS", bootstrap_servers),
            ("KAFKA_API_KEY", api_key),
            ("KAFKA_API_SECRET", api_secret),
        ]
        if not value
    ]
    if missing:
        print(f"ERROR: missing required env vars: {', '.join(missing)}. Check your .env file.")
        sys.exit(1)

    return {
        "bootstrap.servers": bootstrap_servers,
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": api_key,
        "sasl.password": api_secret,
        # client-side batching settings — fine defaults for low-volume simulation
        "client.id": "ecommerce-event-simulator",
        "linger.ms": 50,
    }


def delivery_callback(err: KafkaError, msg) -> None:
    """
    Called by the Kafka client (asynchronously) once a message is actually
    delivered or fails. Without this, produce() failures fail silently.
    """
    if err is not None:
        print(f"  delivery failed: {err}")



class GracefulShutdown:
    """
    Catches Ctrl+C (SIGINT) so we can flush the producer's internal buffer
    before exiting, instead of dropping whatever hasn't been sent yet.
    """

    def __init__(self):
        self.should_stop = False
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame) -> None:
        print("\nShutdown signal received, finishing current batch...")
        self.should_stop = True


def run_producer(rate: float, duration: Optional[int] = None) -> None:
    """
    Main produce loop.

    Args:
        rate: events to produce per second. Sleeps (1/rate) seconds between
            events to approximate this — not perfectly precise under load,
            but accurate enough for a simulator.
        duration: optional, stop automatically after this many seconds.
            If None, runs until Ctrl+C.
    """
    print("Loading reference data pool from MongoDB...")
    pool = load_reference_pool()
    print(f"Loaded {len(pool.user_ids)} users and {len(pool.product_ids)} products.\n")

    producer = Producer(build_producer_config())
    shutdown = GracefulShutdown()

    interval = 1.0 / rate
    sent_count = 0
    error_count = 0
    start_time = time.time()

    print(f"Producing to '{TOPIC_EVENTS}' at ~{rate} events/sec. Press Ctrl+C to stop.\n")

    try:
        while not shutdown.should_stop:
            if duration is not None and (time.time() - start_time) >= duration:
                print(f"\nDuration limit of {duration}s reached, stopping.")
                break

            event = generate_random_event(pool)

            try:
                producer.produce(
                    topic=TOPIC_EVENTS,
                    key=event["user_id"],          # same user's events land on the same partition
                    value=json.dumps(event),
                    callback=delivery_callback,
                )
                sent_count += 1
                if event["type"] == "purchase":
                    order = generate_order(event)
                    producer.produce(
                        topic=TOPIC_ORDERS,
                        key=order["user_id"],          # same user's events land on the same partition
                        value=json.dumps(order),
                        callback=delivery_callback,
                    )

            except BufferError:
                # Local producer queue is full — give Kafka a moment to catch up.
                print("  producer queue full, polling to drain...")
                producer.poll(1)
                error_count += 1
                continue

            # poll(0) processes delivery callbacks without blocking — required
            # periodically or the client never fires delivery_callback at all.
            producer.poll(0)

            if sent_count % 50 == 0:
                elapsed = time.time() - start_time
                print(f"  sent={sent_count}  errors={error_count}  elapsed={elapsed:.0f}s")

            time.sleep(interval)

    finally:
        print(f"\nFlushing remaining messages...")
        producer.flush(timeout=10)
        elapsed = time.time() - start_time
        print(f"Done. sent={sent_count}  errors={error_count}  elapsed={elapsed:.0f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream simulated e-commerce events to Confluent Cloud Kafka.")
    parser.add_argument(
        "--rate",
        type=float,
        default=5.0,
        help="Events per second to produce (default: 5)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Stop automatically after this many seconds (default: run until Ctrl+C)",
    )
    args = parser.parse_args()

    if args.rate <= 0:
        print("ERROR: --rate must be greater than 0")
        sys.exit(1)

    run_producer(rate=args.rate, duration=args.duration)


if __name__ == "__main__":
    main()