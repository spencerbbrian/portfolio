"""
dags/nightly_product_stats.py

Runs daily at 01:00 UTC. For every product, computes:
  - views_7d: count of page_view events in the last 7 days
  - purchases_7d: count of purchase events in the last 7 days
  - conversion_rate: purchases_7d / views_7d (0 if no views)

Updates products.stats with the results using MongoDB's aggregation pipeline
(equivalent to a dbt model — computation happens inside MongoDB, not pulled
into Python and looped over).
"""

from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task

MONGO_CONN_ID = "mongo_default"  # not used directly here — we connect via MONGO_URI env var
LOOKBACK_DAYS = 7


@dag(
    dag_id="nightly_product_stats",
    schedule="0 1 * * *",   # 01:00 UTC daily
    start_date=datetime(2026, 1, 1),
    catchup=False,           # don't backfill missed runs
    tags=["ecommerce", "products", "nightly"],
)
def nightly_product_stats():

    @task
    def compute_and_update_stats() -> dict:
        """
        Single task: connects to MongoDB, aggregates event counts per product
        over the last 7 days, and updates each product's stats field.

        Kept as one task rather than split into compute/write tasks because
        the aggregation result needs to be written back per-product anyway —
        splitting wouldn't reduce work, just add XCom overhead.
        """
        import os
        from pymongo import MongoClient

        from schemas import COLLECTION_EVENTS, COLLECTION_PRODUCTS

        uri = os.environ["MONGO_URI"]
        db_name = os.environ.get("MONGO_DB_NAME", "ecommerce_pipeline")

        client = MongoClient(uri, serverSelectionTimeoutMS=8000)
        db = client[db_name]

        cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
        cutoff_iso = cutoff.isoformat()

        # Aggregation pipeline: group events by product_id and type, count them.
        # This is the MongoDB equivalent of a dbt model — the computation
        # happens inside the database, not in a Python loop.
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": cutoff_iso},
                "type": {"$in": ["page_view", "purchase"]},
                "product_id": {"$ne": None},
            }},
            {"$group": {
                "_id": {"product_id": "$product_id", "type": "$type"},
                "count": {"$sum": 1},
            }},
        ]

        results = list(db[COLLECTION_EVENTS].aggregate(pipeline))

        # Reshape into {product_id: {"views_7d": n, "purchases_7d": n}}
        stats_by_product: dict[str, dict] = {}
        for row in results:
            product_id = row["_id"]["product_id"]
            event_type = row["_id"]["type"]
            count = row["count"]

            if product_id not in stats_by_product:
                stats_by_product[product_id] = {"views_7d": 0, "purchases_7d": 0}

            if event_type == "page_view":
                stats_by_product[product_id]["views_7d"] = count
            elif event_type == "purchase":
                stats_by_product[product_id]["purchases_7d"] = count

        # Write each product's updated stats. Products with zero events in the
        # window are intentionally left alone — resetting them to zero would
        # erase historical stats for slow-moving products between DAG runs
        # that happen to have a quiet week, which isn't the intent here.
        updated_count = 0
        for product_id, stats in stats_by_product.items():
            views = stats["views_7d"]
            purchases = stats["purchases_7d"]
            conversion_rate = round(purchases / views, 4) if views > 0 else 0.0

            db[COLLECTION_PRODUCTS].update_one(
                {"sku": product_id},
                {"$set": {
                    "stats.views_7d": views,
                    "stats.purchases_7d": purchases,
                    "stats.conversion_rate": conversion_rate,
                }},
            )
            updated_count += 1

        client.close()

        return {
            "products_updated": updated_count,
            "cutoff": cutoff_iso,
        }

    compute_and_update_stats()


nightly_product_stats()