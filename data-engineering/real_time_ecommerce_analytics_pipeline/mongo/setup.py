"""
mongo/setup.py

One-time setup script for the e-commerce analytics pipeline's MongoDB Atlas cluster.

Run this once after creating your Atlas cluster to:
  1. Create the four collections (events, orders, products, users) if they don't exist
  2. Create all indexes defined in schemas.py
  3. Print a summary so you can verify everything was created correctly

Usage:
    python mongo/setup.py
    python mongo/setup.py --drop-first   # WARNING: drops collections before recreating
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, TEXT, MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from schemas import (
    COLLECTION_EVENTS,
    COLLECTION_EVENTS_ARCHIVE,
    COLLECTION_ORDERS,
    COLLECTION_PRODUCTS,
    COLLECTION_USERS,
)

load_dotenv()

DB_NAME = os.getenv("MONGO_DB_NAME", "ecommerce_pipeline")
EVENTS_TTL_SECONDS = 60 * 60 * 24 * 90  # 90 days


def get_client() -> MongoClient:
    """Connect to MongoDB Atlas using the URI from the environment."""
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("ERROR: MONGO_URI not found in environment. Check your .env file.")
        sys.exit(1)

    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    try:
        client.admin.command("ping")
    except ConnectionFailure as exc:
        print(f"ERROR: could not connect to MongoDB Atlas — {exc}")
        sys.exit(1)

    return client


def drop_collections(db, collections: list[str]) -> None:
    print("Dropping existing collections...")
    for name in collections:
        db.drop_collection(name)
        print(f"  dropped: {name}")


def create_collections(db, collections: list[str]) -> None:
    existing = set(db.list_collection_names())
    for name in collections:
        if name in existing:
            print(f"  exists already, skipping create: {name}")
            continue
        db.create_collection(name)
        print(f"  created: {name}")


def setup_events_indexes(db) -> None:
    coll = db[COLLECTION_EVENTS]
    print(f"\nIndexes for '{COLLECTION_EVENTS}':")

    coll.create_index(
        [("type", ASCENDING), ("timestamp", DESCENDING)],
        name="type_timestamp_idx",
    )
    print("  created: type_timestamp_idx")

    coll.create_index(
        [("user_id", ASCENDING)],
        name="user_id_idx",
    )
    print("  created: user_id_idx")

    # TTL index — MongoDB auto-deletes documents 90 days after their timestamp.
    # NOTE: the field must be a BSON date for TTL to work. If you're storing
    # timestamp as an ISO string, convert to datetime before inserting, or
    # add a separate `expires_at` datetime field and TTL-index that instead.
    coll.create_index(
        [("timestamp", ASCENDING)],
        name="timestamp_ttl_idx",
        expireAfterSeconds=EVENTS_TTL_SECONDS,
    )
    print(f"  created: timestamp_ttl_idx (TTL = {EVENTS_TTL_SECONDS}s / 90 days)")


def setup_orders_indexes(db) -> None:
    coll = db[COLLECTION_ORDERS]
    print(f"\nIndexes for '{COLLECTION_ORDERS}':")

    coll.create_index(
        [("order_id", ASCENDING)],
        name="order_id_unique_idx",
        unique=True,
    )
    print("  created: order_id_unique_idx (unique)")

    coll.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        name="user_id_created_at_idx",
    )
    print("  created: user_id_created_at_idx (compound)")

    coll.create_index(
        [("status", ASCENDING)],
        name="status_idx",
    )
    print("  created: status_idx")


def setup_products_indexes(db) -> None:
    coll = db[COLLECTION_PRODUCTS]
    print(f"\nIndexes for '{COLLECTION_PRODUCTS}':")

    coll.create_index(
        [("sku", ASCENDING)],
        name="sku_unique_idx",
        unique=True,
    )
    print("  created: sku_unique_idx (unique)")

    coll.create_index(
        [("name", TEXT)],
        name="name_text_idx",
    )
    print("  created: name_text_idx (full-text search)")

    coll.create_index(
        [("tags", ASCENDING)],
        name="tags_idx",
    )
    print("  created: tags_idx (multikey)")


def setup_users_indexes(db) -> None:
    coll = db[COLLECTION_USERS]
    print(f"\nIndexes for '{COLLECTION_USERS}':")

    coll.create_index(
        [("user_id", ASCENDING)],
        name="user_id_unique_idx",
        unique=True,
    )
    print("  created: user_id_unique_idx (unique)")

    coll.create_index(
        [("email", ASCENDING)],
        name="email_unique_idx",
        unique=True,
    )
    print("  created: email_unique_idx (unique)")

    coll.create_index(
        [("segments", ASCENDING)],
        name="segments_idx",
    )
    print("  created: segments_idx (multikey)")


def print_summary(db) -> None:
    print("\n" + "=" * 50)
    print(f"Summary for database '{DB_NAME}':")
    print("=" * 50)
    for name in db.list_collection_names():
        count = db[name].estimated_document_count()
        indexes = list(db[name].list_indexes())
        print(f"\n{name}  ({count} documents)")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx.get('key')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up MongoDB Atlas for the e-commerce pipeline.")
    parser.add_argument(
        "--drop-first",
        action="store_true",
        help="Drop existing collections before recreating them. Destroys all data.",
    )
    args = parser.parse_args()

    all_collections = [
        COLLECTION_EVENTS,
        COLLECTION_ORDERS,
        COLLECTION_PRODUCTS,
        COLLECTION_USERS,
        COLLECTION_EVENTS_ARCHIVE,
    ]

    client = get_client()
    db = client[DB_NAME]

    print(f"Connected to MongoDB Atlas. Using database '{DB_NAME}'.\n")

    if args.drop_first:
        confirm = input(
            f"This will DROP {len(all_collections)} collections in '{DB_NAME}'. Type 'yes' to confirm: "
        )
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            sys.exit(0)
        drop_collections(db, all_collections)

    print("\nCreating collections...")
    create_collections(db, all_collections)

    try:
        setup_events_indexes(db)
        setup_orders_indexes(db)
        setup_products_indexes(db)
        setup_users_indexes(db)
    except OperationFailure as exc:
        print(f"\nERROR while creating indexes: {exc}")
        sys.exit(1)

    print_summary(db)
    print("\nSetup complete.")

    client.close()


if __name__ == "__main__":
    main()