# Churn Radar

Customer health-scoring and churn-prevention platform for a simulated SaaS product.
Ingests product usage and billing events, models a composite health score and churn-risk
tier in dbt, orchestrates the pipeline with Dagster (asset graph, a sensor, asset checks),
and reverse-ETLs the results into HubSpot (CRM) and Slack.

An asset-aware orchestrator (as opposed to Airflow's task-based scheduling), and reverse
ETL moving data back out of the warehouse into the tools a team actually uses, not
just into dashboards.

**Warehouse: BigQuery** (same GCP project/account as
`data-engineering/b2b-realtime-spend-GCP`).

## Architecture

```
source_api/  (fake SaaS product, FastAPI + SQLite)
    -> airbyte/  (config-as-code, incremental sync)
        -> BigQuery (raw landing)
            -> dbt/  (staging -> intermediate -> marts: health score, churn risk)
                -> reverse_etl/  (HubSpot contact properties + Slack alerts)

dagster/  orchestrates all of the above: schedule, a sensor that fires on new raw
          data, and asset checks gating the churn-risk mart before reverse ETL runs.
```

## Build status

Building step by step, in this order:

1. **`source_api/`** -- fake SaaS product + synthetic data generator. *In progress.*
2. `dbt/` -- staging/intermediate/marts modeling the health score and churn risk.
3. `airbyte/` -- config-as-code, source API -> BigQuery.
4. `dagster/` -- orchestration: asset graph, schedule, sensor, asset checks.
5. `reverse_etl/` -- HubSpot + Slack sync.

## Why the synthetic data isn't random noise

Each generated customer is secretly assigned one of three behavior patterns --
healthy, at_risk, or churned -- that shapes how their login frequency, feature usage,
support tickets, and billing events are generated (e.g. at-risk customers show a real
drop-off in activity over their last 30-45 days, a higher support-ticket rate, and
often a failed payment before canceling). That internal label is never written to the
database or exposed through the API -- it exists only so the health-score model in
dbt has genuine behavioral signal to detect, instead of scoring pure randomness.
