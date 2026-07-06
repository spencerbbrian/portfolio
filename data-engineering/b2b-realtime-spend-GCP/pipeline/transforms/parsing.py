"""
parsing.py

First transform in the pipeline. Reads raw bytes from Pub/Sub, attempts to
parse them as JSON, and routes each message to one of two outputs:

    - "valid":      a well-formed transaction dict, ready for feature engineering
    - "dead_letter": the raw bytes + error info, written to a dead-letter sink
                     for inspection (local file during dev, GCS/BQ when deployed)

This pattern — called the dead-letter pattern — is standard in production
streaming pipelines. Instead of crashing the entire pipeline on one bad
message, you route failures to a separate sink so they can be inspected and
reprocessed later without data loss.

Apache Beam supports multiple outputs from one DoFn via tagged outputs.
We define two tags here: VALID_TAG and DEAD_LETTER_TAG. The main pipeline
uses these tags to split the PCollection after this transform.
"""

import json
import logging

import apache_beam as beam
from apache_beam import pvalue

# Tags used to label the two output streams from ParseTransactionFn.
# The main pipeline uses these to route records after parsing.
VALID_TAG = "valid"
DEAD_LETTER_TAG = "dead_letter"

# Minimum fields that must be present for a transaction to be considered valid.
# If any of these are missing, the record goes to the dead-letter output.
REQUIRED_FIELDS = {
    "transaction_id",
    "company_id",
    "vendor_id",
    "vendor_category",
    "vendor_risk_tier",
    "amount_usd",
    "timestamp",
    "baseline_monthly_spend",
    "company_size_tier",
}


class ParseTransactionFn(beam.DoFn):
    """
    DoFn that parses raw Pub/Sub message bytes into a transaction dict.

    Yields to VALID_TAG on success, DEAD_LETTER_TAG on any failure.
    The main pipeline calls beam.ParDo(ParseTransactionFn()).with_outputs()
    to get access to both output streams separately.
    """

    def process(self, element, *args, **kwargs):
        """
        element: raw bytes from Pub/Sub (the message payload).
        Apache Beam passes one element at a time to process().
        """
        raw = None
        try:
            # Pub/Sub messages arrive as bytes — decode to string first
            if isinstance(element, bytes):
                raw = element.decode("utf-8")
            else:
                raw = str(element)

            txn = json.loads(raw)

            # Validate required fields are present
            missing = REQUIRED_FIELDS - set(txn.keys())
            if missing:
                raise ValueError(f"Missing required fields: {missing}")

            # Coerce numeric fields — CSV-sourced data may come in as strings
            txn["amount_usd"] = float(txn["amount_usd"])
            txn["baseline_monthly_spend"] = float(txn["baseline_monthly_spend"])

            # Yield to the valid output tag
            yield pvalue.TaggedOutput(VALID_TAG, txn)

        except Exception as e:
            logging.warning(f"Dead-lettering message due to: {e} | raw: {raw[:200] if raw else element}")
            yield pvalue.TaggedOutput(
                DEAD_LETTER_TAG,
                {
                    "raw_message": raw or str(element),
                    "error": str(e),
                },
            )