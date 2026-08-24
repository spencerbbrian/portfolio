# Churn Radar

Customer health-scoring and churn-prevention platform for a simulated SaaS product.
Ingests product usage and billing events, models a composite health score and churn-risk
tier in dbt, orchestrates the pipeline with Dagster (asset graph, a sensor, asset checks),
and reverse-ETLs the results into HubSpot (CRM) and Slack.

Built to demonstrate two things the rest of this portfolio didn't yet cover: an
asset-aware orchestrator (as opposed to Airflow's task-based scheduling), and reverse
ETL moving data back out of the warehouse into the tools a team actually uses, not
just into dashboards.

**Warehouse: BigQuery** (same GCP project/account as
`data-engineering/b2b-realtime-spend-GCP`).

## Architecture

```
source_api/  (fake SaaS product, FastAPI + SQLite, deployed on Render)
    -> airbyte/  (config-as-code custom connector, Airbyte Cloud)
        -> BigQuery (raw landing: churn_radar_raw)
            -> dbt/  (staging -> intermediate -> marts: health score, churn risk)
                -> reverse_etl/  (HubSpot contact properties + Slack alerts)

dagster/  orchestrates all of the above: schedule, a sensor that fires on new raw
          data, and asset checks gating the churn-risk mart before reverse ETL runs.
```

`source_api/` runs as a public Render web service so Airbyte Cloud can reach it
directly -- no local process or tunnel required for a sync to succeed.

## Build status

Building step by step, in this order:

1. **`source_api/`** -- fake SaaS product + synthetic data generator. *Done -- deployed on Render.*
2. **`dbt/`** -- staging/intermediate/marts modeling the health score and churn risk. *Done -- now runnable, raw data is landing in BigQuery.*
3. **`airbyte/`** -- config-as-code custom connector, source API -> BigQuery. *Done -- built and published in Airbyte Cloud, manifest saved in this repo.*
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

## Why Airbyte Cloud instead of a local install

The connector was originally built and tested locally via `abctl` (self-hosted Airbyte
on Kubernetes-in-Docker through OrbStack). That local install's "Publish to organization"
action hit a reproducible `errors.http.internalServerError`, confirmed across multiple
reinstalls. Rather than work around it with a stand-in script, the fix was to move to
the real, hosted Airbyte Cloud -- same connector, same manifest, genuinely working publish
path. The local install was torn down (`abctl local uninstall --persisted` +
`docker system prune -a`) once Cloud was confirmed working, reclaiming ~5 GB.

## Known limitation: sync mode is Full Refresh | Overwrite, not incremental

The custom connector currently issues a plain `GET` on every sync -- it doesn't inject a
`?since=<cursor>` parameter based on the last sync's high-water mark, even though
`source_api` already supports that cursor param for pagination. Because of that, every
stream runs as **Full Refresh | Overwrite**: each sync replaces the BigQuery table with
a fresh full pull, which is correct and duplicate-free, just not incremental. Adding a
declarative `IncrementalSync` component (cursor field + dynamic request parameter) to
`airbyte/churn_radar_source_manifest.yaml` is a legitimate future upgrade, not required
for correctness today.