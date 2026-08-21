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
- **Snapshots** (`snapshots/`) — `snap_sellers`, an SCD Type 2 history of seller
  location fields, snapshotted directly from the raw source.
- **Semantic Layer** (`models/semantic/`) — MetricFlow semantic models and metrics
  (`revenue`, `order_count`, `average_order_value`, `on_time_delivery_rate`,
  `attributed_revenue_by_channel`) on top of the marts.
- **Exposures** (`models/exposures.yml`) — documents the dashboards/consumers that sit
  downstream of the marts and the semantic layer, so `dbt docs generate` shows a full
  lineage graph from raw source to a dashboard someone actually opens.

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
  - `dbt_cd.yml` — on merge to `main`: `dbt run --target prod`, `dbt snapshot --target
    prod`, then the Great Expectations suite against the freshly built `PROD` tables,
    then `dbt docs generate` published to GitHub Pages. A failed dbt test or a failed
    expectation fails the job.

## Running locally

```bash
dbt deps
dbt seed        # if using local seeds instead of the RAW Snowflake sources
dbt run
dbt snapshot    # captures the current SCD Type 2 state into snap_sellers
dbt test
```

See `quality/README.md` for running the Great Expectations checks locally.

### Querying the semantic layer

Querying metrics locally requires the separate MetricFlow query engine (not bundled
with plain `dbt-core`). Note: `dbt sl` is a dbt Cloud CLI feature only -- with plain
open-source `dbt-core`, you install `dbt-metricflow` and query through its own
standalone `mf` command instead:

```bash
pip install dbt-metricflow

dbt parse                                                   # generates target/semantic_manifest.json, which `mf` reads
mf validate-configs                                         # sanity-check the semantic model/metric definitions
mf query --metrics revenue --group-by metric_time__day
mf query --metrics attributed_revenue_by_channel --group-by marketing_channel
mf query --metrics on_time_delivery_rate --group-by metric_time__month
```

### Hosted docs

`dbt_cd.yml` runs `dbt docs generate` and publishes the result to GitHub Pages
(`gh-pages` branch, `/olist-docs`) on every merge to `main`. One manual step is
required the first time: after the first successful CD run creates the `gh-pages`
branch, enable Pages in the repo's Settings → Pages, with source set to the
`gh-pages` branch. After that it stays up to date automatically.

## Project history

- **Stage 1** — sync data into Snowflake via dbt seeds (Python-generated sample data),
  configure `DBT_DEVELOPER` role / `DBT_ANALYTICS` database.
- **Stage 2** — incremental models for frequently updated data, materialized views for
  aggregates, source freshness tests, and singular tests (e.g. every customer has at
  least one order; completed-order counts reconcile between fact and summary tables).
- **Current** — added the Great Expectations data-quality layer, SCD Type 2 seller
  history via snapshots, a dbt Semantic Layer (MetricFlow) on top of the marts,
  exposures documenting downstream consumers, and hosted dbt docs on GitHub Pages.
