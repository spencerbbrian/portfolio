"""
mongo/seed.py

Seeds the e-commerce analytics pipeline's MongoDB Atlas cluster with reference data:
  - 100 products across 5 categories
  - 500 users with realistic signup dates spread over the past 12 months

This data is the foundation everything else depends on: the event simulator
references these product_ids and user_ids, and orders reference both.

Run this AFTER mongo/setup.py (collections and indexes must exist first).

Usage:
    python mongo/seed.py
    python mongo/seed.py --products 200 --users 1000   # custom volumes
    python mongo/seed.py --wipe                          # clear before reseeding
"""

import argparse
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from schemas import COLLECTION_PRODUCTS, COLLECTION_USERS

load_dotenv()
fake = Faker()

DB_NAME = os.getenv("MONGO_DB_NAME", "ecommerce_pipeline")

CATEGORIES = [
    {"id": "cat_footwear", "name": "Footwear"},
    {"id": "cat_apparel", "name": "Apparel"},
    {"id": "cat_electronics", "name": "Electronics"},
    {"id": "cat_home", "name": "Home & Kitchen"},
    {"id": "cat_beauty", "name": "Beauty"},
]

PRODUCT_NOUNS = {
    "cat_footwear": ["running shoes", "sneakers", "boots", "sandals", "loafers"],
    "cat_apparel": ["t-shirt", "hoodie", "jacket", "jeans", "joggers"],
    "cat_electronics": ["headphones", "smartwatch", "speaker", "charger", "tablet stand"],
    "cat_home": ["mug", "blanket", "candle", "cutting board", "lamp"],
    "cat_beauty": ["face cream", "shampoo", "lip balm", "serum", "body wash"],
}

ADJECTIVES = ["Pro", "Classic", "Eco", "Premium", "Compact", "Everyday", "Deluxe", "Essential"]

TAG_POOL = ["new", "sale", "bestseller", "limited", "eco-friendly", "trending", "restocked"]


def get_client() -> MongoClient:
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


def generate_sku(category_id: str, index: int) -> str:
    cat_code = category_id.replace("cat_", "").upper()[:4]
    return f"{cat_code}-{index:04d}"


def generate_products(count: int) -> list[dict]:
    products = []
    per_category = max(1, count // len(CATEGORIES)) #safe-fail to have min 1

    index = 1
    for category in CATEGORIES:
        nouns = PRODUCT_NOUNS[category["id"]]
        for _ in range(per_category):
            noun = random.choice(nouns)
            adjective = random.choice(ADJECTIVES)
            name = f"{adjective} {noun}".title()

            price = round(random.uniform(9.99, 249.99), 2)
            quantity = random.randint(0, 300)
            reserved = random.randint(0, min(10, quantity)) if quantity > 0 else 0

            tags = random.sample(TAG_POOL, k=random.randint(1, 3))

            product = {
                "sku": generate_sku(category["id"], index),
                "name": name,
                "category": category,
                "price": price,
                "inventory": {
                    "quantity": quantity,
                    "reserved": reserved,
                    "in_stock": quantity > reserved,
                },
                "tags": tags,
                # stats start at zero — populated later by the nightly Airflow DAG
                "stats": {
                    "views_7d": 0,
                    "purchases_7d": 0,
                    "conversion_rate": 0.0,
                },
            }
            products.append(product)
            index += 1

    # top up to exact count if division left a remainder
    while len(products) < count:
        category = random.choice(CATEGORIES)
        noun = random.choice(PRODUCT_NOUNS[category["id"]])
        adjective = random.choice(ADJECTIVES)
        products.append({
            "sku": generate_sku(category["id"], index),
            "name": f"{adjective} {noun}".title(),
            "category": category,
            "price": round(random.uniform(9.99, 249.99), 2),
            "inventory": {"quantity": 50, "reserved": 0, "in_stock": True},
            "tags": random.sample(TAG_POOL, k=2),
            "stats": {"views_7d": 0, "purchases_7d": 0, "conversion_rate": 0.0},
        })
        index += 1

    return products[:count]


def generate_users(count: int) -> list[dict]:
    users = []
    now = datetime.now(timezone.utc)

    for _ in range(count):
        signup_days_ago = random.randint(1, 365)
        created_at = now - timedelta(days=signup_days_ago)

        user = {
            "user_id": f"usr_{uuid.uuid4().hex[:12]}",
            "email": fake.unique.email(),
            # segments start empty — populated nightly by the RFM Airflow DAG
            "segments": [],
            "recent_orders": [],
            "rfm": {
                "recency_days": 0,
                "frequency": 0,
                "monetary_total": 0.0,
            },
            "created_at": created_at.isoformat(),
        }
        users.append(user)

    return users


def seed_products(db, count: int, wipe: bool) -> None:
    coll = db[COLLECTION_PRODUCTS]

    if wipe:
        deleted = coll.delete_many({}).deleted_count
        print(f"  wiped {deleted} existing products")

    existing = coll.count_documents({})
    if existing > 0 and not wipe:
        print(f"  found {existing} existing products, skipping seed (use --wipe to reseed)")
        return

    products = generate_products(count)
    result = coll.insert_many(products)
    print(f"  inserted {len(result.inserted_ids)} products across {len(CATEGORIES)} categories")


def seed_users(db, count: int, wipe: bool) -> None:
    coll = db[COLLECTION_USERS]

    if wipe:
        deleted = coll.delete_many({}).deleted_count
        print(f"  wiped {deleted} existing users")

    existing = coll.count_documents({})
    if existing > 0 and not wipe:
        print(f"  found {existing} existing users, skipping seed (use --wipe to reseed)")
        return

    users = generate_users(count)
    result = coll.insert_many(users)
    print(f"  inserted {len(result.inserted_ids)} users")


def print_summary(db) -> None:
    print("\n" + "=" * 50)
    print("Seed summary")
    print("=" * 50)

    products_coll = db[COLLECTION_PRODUCTS]
    users_coll = db[COLLECTION_USERS]

    print(f"\nproducts: {products_coll.count_documents({})} documents")
    for category in CATEGORIES:
        n = products_coll.count_documents({"category.id": category["id"]})
        print(f"  {category['name']}: {n}")

    print(f"\nusers: {users_coll.count_documents({})} documents")
    sample = users_coll.find_one({}, {"_id": 0, "user_id": 1, "email": 1})
    if sample:
        print(f"  sample: {sample}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed reference data for the e-commerce pipeline.")
    parser.add_argument("--products", type=int, default=100, help="Number of products to seed (default: 100)")
    parser.add_argument("--users", type=int, default=500, help="Number of users to seed (default: 500)")
    parser.add_argument("--wipe", action="store_true", help="Delete existing products/users before seeding")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible data")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)

    client = get_client()
    db = client[DB_NAME]

    print(f"Connected to MongoDB Atlas. Using database '{DB_NAME}'.\n")

    print(f"Seeding {args.products} products...")
    seed_products(db, args.products, args.wipe)

    print(f"\nSeeding {args.users} users...")
    seed_users(db, args.users, args.wipe)

    print_summary(db)
    print("\nSeed complete.")

    client.close()


if __name__ == "__main__":
    main()