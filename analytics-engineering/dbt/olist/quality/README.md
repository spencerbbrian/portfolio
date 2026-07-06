# Data Quality Layer (Great Expectations)

dbt's native tests (`not_null`, `unique`, `accepted_values`, relationship tests — see
`models/*/*.yml`) are schema-level checks: they run per-column, per-row, against a single
table, at build time. They're good at "is this column ever null" and bad at "is this
column's *distribution* behaving normally" or "does this row make sense relative to
another column on the same row."

This folder adds a second, complementary layer using [Great Expectations](https://greatexpectations.io/)
that runs **after** `dbt run` has materialized the mart tables in Snowflake, and checks
the kinds of things dbt's generic tests can't easily express:

| Check type | Example | dbt-native? |
|---|---|---|
| Column not null / unique / accepted values | `order_id` is unique | Yes — already in `.yml` schema files |
| Row-count / volume anomaly | `fct_orders` has 1,000–500,000 rows | No — needs `dbt_utils`/Elementary or an external tool |
| Cross-column consistency on the same row | `delivered_customer_date >= purchase_date` | Only via a custom singular test macro |
| Statistical drift | average order value stays within a known band | No |
| Soft/percentage-based tolerance | 95%+ of `marketing_channel` values are in a known set, rather than a hard 100% | No (dbt tests are pass/fail per row) |

## Layout

```
quality/
  context.py            # builds a GX Data Context + Snowflake datasource from env vars
  run_quality_checks.py # entry point: runs every suite below, exits non-zero on failure
  suites/
    fct_orders.py               # volume, financial sanity, delivery-date ordering, AOV drift
    dim_sellers.py               # seller_id uniqueness, funnel/channel value sets
    fct_b2b2c_attribution.py     # attribution revenue sanity + row-count checks
  requirements.txt
```

Each suite module is just a `TABLE_NAME`, a `SUITE_NAME`, and a plain list of
`(expectation_type, kwargs)` tuples — adding a new check means appending one line, not
writing new plumbing.

## Wiring

Added as a step in `.github/workflows/dbt_cd.yml`, running immediately after
`dbt run --target prod` — so it validates the tables that were just built on `main`,
using the same Snowflake secrets already configured for dbt. A failed expectation fails
the job the same way a failed `dbt test` would.

## Running locally

```bash
cd analytics-engineering/dbt/olist/quality
pip install -r requirements.txt

export SNOWFLAKE_ACCOUNT=...
export SNOWFLAKE_USER=...
export SNOWFLAKE_PASSWORD=...
export SNOWFLAKE_ROLE=...
export SNOWFLAKE_WAREHOUSE=...
export SNOWFLAKE_SCHEMA=PROD   # or DEV

python run_quality_checks.py
```

Data Docs (an HTML report of every expectation and its result) are written locally to
`quality/gx/uncommitted/data_docs/` — open `index.html` to browse results.

## Why Great Expectations here instead of Elementary

Elementary plugs directly into dbt's own test results and is arguably the more
"native" choice for a dbt project. Great Expectations was used instead specifically to
show comfort with a standalone, Python-based data quality framework that isn't wired
through dbt at all — the kind of tool that shows up in ingestion/ELT pipelines that
have no dbt layer, not just warehouse marts.
