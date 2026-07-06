# Olist E-Commerce Analytics (dbt + Snowflake)

Batch ELT/warehouse modeling project on the Olist Brazilian e-commerce dataset, extended
with a B2B2C seller-attribution angle (linking end-customer orders back to the
marketing channel and sales rep that acquired the seller who fulfilled them).

## Architecture

```
sources (RAW schema)
  → staging (views, 1:1 with source tables, light renaming/casting)
  → intermediate (views, aggregation/joining logic)
  → marts (tables, one row per business entity)
```

- **Staging** (`models/staging/`) — `stg_orders`, `stg_customers`, `stg_sellers`,
  `stg_order_items`, `stg_order_payments`, `stg_order_reviews`, `stg_products`,
  `stg_geolocation`, `stg_closed_deals`, `stg_marketing_leads`,
  `stg_product_category_name_translation`.
- **Intermediate** (`models/intermediate/`) — `int_order_items_aggregated` (order-level
  rollups of price/freight/item counts), `int_closed_market_qualified_leads`
  (marketing → sales → closed-deal funnel per seller).
- **Marts** (`models/mart/`) — `fct_orders` (order grain, delivery performance),
  `dim_sellers` (seller grain, acquisition channel), `fct_b2b2c_attribution` (order ×
  seller grain, ties revenue back to marketing channel and sales rep).

## Testing & CI/CD

- **dbt-native tests** — `unique`/`not_null`/`accepted_values` on every mart column
  that needs one (see each model's `.yml` schema file).
- **Great Expectations** (`quality/`) — a second, complementary layer covering
  row-count/volume anomalies, cross-column temporal checks, financial-value sanity, and
  distribution drift that dbt's generic tests don't express well. See
  `quality/README.md` for the full breakdown of what lives where and why.
- **GitHub Actions**:
  - `dbt_ci.yml` — `dbt compile` + `dbt test` against the `dev` target on every PR
    touching this project.
  - `dbt_cd.yml` — on merge to `main`: `dbt run --target prod`, then the Great
    Expectations suite against the freshly built `PROD` tables. Either a failed dbt
    test or a failed expectation fails the job.

## Running locally

```bash
dbt deps
dbt seed        # if using local seeds instead of the RAW Snowflake sources
dbt run
dbt test
```

See `quality/README.md` for running the Great Expectations checks locally.

## Project history

- **Stage 1** — sync data into Snowflake via dbt seeds (Python-generated sample data),
  configure `DBT_DEVELOPER` role / `DBT_ANALYTICS` database.
- **Stage 2** — incremental models for frequently updated data, materialized views for
  aggregates, source freshness tests, and singular tests (e.g. every customer has at
  least one order; completed-order counts reconcile between fact and summary tables).
- **Current** — added the Great Expectations data-quality layer described above.
