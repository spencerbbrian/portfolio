"""
windowing.py

Windowed aggregation transform. Groups scored transactions by company over a
fixed time window and computes per-company spend/risk summaries.

Why windowing:
    A streaming pipeline processes one record at a time. To answer "how much
    did company_0012 spend in the last 5 minutes" you need to group records
    over time — that's what Beam windows do. A fixed window of 5 minutes
    means: take all records that arrived between T and T+5min, group them,
    aggregate.

Window size:
    5 minutes for local dev (produces aggregates quickly so you can see
    results in BigQuery fast). In production you'd likely use 1-hour windows
    for meaningful spend summaries.

Output schema (one row per company per window):
    window_start, window_end, company_id, company_name, company_size_tier,
    transaction_count, total_amount_usd, max_amount_usd, avg_amount_usd,
    risk_flagged_count, any_risk_flag
"""

import logging
from datetime import datetime, timezone

import apache_beam as beam
from apache_beam import window
from apache_beam.transforms.core import DoFn


WINDOW_SIZE_SECONDS = 5 * 60  # 5 minutes


class ExtractCompanyKeyFn(beam.DoFn):
    """
    DoFn that extracts a (company_id, transaction) key-value pair from a
    scored transaction dict.

    Beam's GroupByKey and window operations require the PCollection to be
    in (key, value) format. This transform sets company_id as the key so
    all transactions for the same company end up in the same group within
    each window.
    """

    def process(self, txn: dict, *args, **kwargs):
        yield (txn["company_id"], txn)


class AggregateWindowFn(beam.DoFn):
    """
    DoFn that receives all transactions for one company in one window and
    computes aggregate metrics.

    After GroupByKey + windowing, Beam calls process() with:
        element: (company_id, iterable_of_transactions)
        window: the Window object containing start/end timestamps

    We use the window parameter to record which time window this aggregate
    covers, so the BigQuery row has a meaningful window_start and window_end.
    """

    def process(self, element, window=beam.DoFn.WindowParam, *args, **kwargs):
        company_id, transactions = element
        txn_list = list(transactions)

        if not txn_list:
            return

        # Extract window boundaries — Beam timestamps are in seconds since epoch
        window_start = datetime.fromtimestamp(
            window.start.micros / 1e6, tz=timezone.utc
        ).isoformat()
        window_end = datetime.fromtimestamp(
            window.end.micros / 1e6, tz=timezone.utc
        ).isoformat()

        amounts = [float(t["amount_usd"]) for t in txn_list]
        risk_flagged = [t for t in txn_list if t.get("risk_flag", False)]

        # Use the first transaction's company metadata for the aggregate row
        first = txn_list[0]

        aggregate = {
            "window_start": window_start,
            "window_end": window_end,
            "company_id": company_id,
            "company_name": first.get("company_name", ""),
            "company_size_tier": first.get("company_size_tier", ""),
            "transaction_count": len(txn_list),
            "total_amount_usd": round(sum(amounts), 2),
            "max_amount_usd": round(max(amounts), 2),
            "avg_amount_usd": round(sum(amounts) / len(amounts), 2),
            "risk_flagged_count": len(risk_flagged),
            "any_risk_flag": len(risk_flagged) > 0,
        }

        logging.info(
            f"Window aggregate | {company_id} | "
            f"{len(txn_list)} txns | "
            f"${aggregate['total_amount_usd']} total | "
            f"{len(risk_flagged)} flagged"
        )

        yield aggregate


def build_windowed_aggregates(scored_transactions):
    """
    Takes a PCollection of scored transaction dicts and returns a PCollection
    of per-company window aggregates.

    Pipeline steps:
        1. Apply fixed windows (5 min)
        2. Extract (company_id, txn) key-value pairs
        3. GroupByKey — groups all txns for same company in same window
        4. Aggregate — compute metrics per group
    """
    return (
        scored_transactions
        | "ApplyFixedWindows" >> beam.WindowInto(
            window.FixedWindows(WINDOW_SIZE_SECONDS)
        )
        | "ExtractCompanyKey" >> beam.ParDo(ExtractCompanyKeyFn())
        | "GroupByCompany" >> beam.GroupByKey()
        | "AggregateWindow" >> beam.ParDo(AggregateWindowFn())
    )