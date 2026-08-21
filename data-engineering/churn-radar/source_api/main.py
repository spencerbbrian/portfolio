"""
FastAPI app standing in for a real SaaS product's API -- this is the
"source system" the ingestion tool (Airbyte) pulls from later. Serves
customers, billing_events, and usage_events out of the SQLite database
built by data_generator.py, with cursor-based pagination on an
updated_at/created_at field -- the same pattern a real incremental REST API
source would use, and what Airbyte's incremental sync will key off of.
"""
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from data_generator import build_database

DB_PATH = Path(__file__).parent / "data.db"

app = FastAPI(title="Churn Radar Source API", version="1.0.0")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def paginated_query(table: str, cursor_field: str, since: Optional[str], limit: int):
    conn = get_connection()
    cur = conn.cursor()
    if since:
        cur.execute(
            f"SELECT * FROM {table} WHERE {cursor_field} > ? ORDER BY {cursor_field} ASC LIMIT ?",
            (since, limit),
        )
    else:
        cur.execute(f"SELECT * FROM {table} ORDER BY {cursor_field} ASC LIMIT ?", (limit,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


@app.on_event("startup")
def ensure_database_exists():
    if not DB_PATH.exists():
        build_database()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/admin/regenerate")
def regenerate():
    """Wipes and regenerates the synthetic dataset -- handy for local dev/demos."""
    build_database()
    return {"status": "regenerated"}


@app.get("/customers")
def list_customers(
    since: Optional[str] = Query(None, description="ISO timestamp cursor -- only rows updated after this"),
    limit: int = Query(200, le=1000),
):
    return JSONResponse(paginated_query("customers", "updated_at", since, limit))


@app.get("/events/billing")
def list_billing_events(
    since: Optional[str] = Query(None, description="ISO timestamp cursor -- only rows created after this"),
    limit: int = Query(500, le=2000),
):
    return JSONResponse(paginated_query("billing_events", "created_at", since, limit))


@app.get("/events/usage")
def list_usage_events(
    since: Optional[str] = Query(None, description="ISO timestamp cursor -- only rows created after this"),
    limit: int = Query(500, le=2000),
):
    return JSONResponse(paginated_query("usage_events", "created_at", since, limit))
