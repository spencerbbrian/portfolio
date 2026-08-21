# Churn Radar dbt Project (BigQuery)

Turns raw usage/billing events (landed in BigQuery by Airbyte) into a per-customer
health score and churn-risk tier.

## Architecture

```
sources (churn_radar_raw dataset, landed by Airbyte)
  -> staging (views, 1:1 rename/cast: stg_customers, stg_billing_events, stg_usage_events)
  -> intermediate (views, feature engineering)
       int_customer_engagement_features  -- login frequency, days since last login, feature adoption
       int_support_ticket_features       -- open/resolved ticket counts
       int_customer_billing_features     -- payment failures, upgrades, downgrades, cancellation date
  -> marts (tables)
       dim_customers    -- one row per customer, descriptive + lifetime billing counts
       fct_churn_risk   -- one row per customer: health_score + churn_risk_tier
```

## The health score

`macros/health_score_weighting.sql` holds the whole scoring formula in one place: starts
at a neutral 50 and adds/subtracts capped points per signal (recent logins, days since
last login, feature adoption breadth, open support tickets, payment failures,
upgrades/downgrades). It's a rules-based, fully explainable score on purpose -- every
point is traceable to a specific behavior -- rather than a black-box model. That's the
standard first pass for a health score in a real company, before anyone invests in
training an ML model on top of it (which this project *could* support later, since the
generated data has real historical cancellation dates to train against).

`fct_churn_risk` only computes `health_score` for `status = 'active'` customers --
someone who already canceled doesn't need a forward-looking score, they need a
`churn_risk_tier` of `'Churned'` instead, which is handled directly in the tier logic.

## Running locally

Requires `dbt-bigquery` instead of `dbt-snowflake`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install dbt-bigquery

dbt debug     # confirms the BigQuery connection before anything else
dbt build     # runs models + tests together, in dependency order
```

Your `~/.dbt/profiles.yml` needs a `churn_radar` profile shaped like this (using a GCP
service account, matching what `b2b-realtime-spend-GCP` already uses -- reuse that same
service account rather than creating a new one):

```yaml
churn_radar:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: your-gcp-project-id
      dataset: churn_radar_dev
      keyfile: /path/to/your/service-account-key.json
      threads: 4
```

## Not built yet

This project doesn't have raw data to run against until the Airbyte sync (next step)
actually lands rows into `churn_radar_raw`. Until then, `dbt debug` will succeed but
`dbt build` will fail on missing source tables -- that's expected, not a bug.
