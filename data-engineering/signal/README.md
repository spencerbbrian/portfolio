# Signal

Telecom subscriber intelligence platform built on synthetic data: a fake phone
company's subscribers, plans, devices, usage events, and support tickets,
modeled through a Data Vault 2.0 raw layer and Kimball dimensional marts,
served through the dbt Semantic Layer. Built as one coherent system, not two
competing modeling philosophies -- the point is knowing when to use each.

Built to demonstrate three things this portfolio didn't yet cover: Data Vault
2.0 (hubs, links, satellites) alongside Kimball star-schema marts in a single
project, the dbt Semantic Layer / MetricFlow for defining a metric once and
reusing it everywhere, and dbt contracts enforced and proven in CI.

**Warehouse: Snowflake.**

## Architecture

```
generate_data/  (Python + Faker, synthetic telecom data -> CSVs)
    -> load_to_snowflake.py  (write_pandas bulk load)
        -> Snowflake SIGNAL_DB.RAW  (raw landing tables)
            -> dbt staging  (light rename/cast, one model per raw source)
                -> dbt raw_vault
                     hubs/        (pure business keys: subscriber, plan, device, ticket)
                     links/       (relationships between hubs)
                     satellites/  (descriptive attributes + full history)
                -> dbt marts  (built from the vault, never from raw)
                     dims/   dim_subscriber (SCD2), dim_plan, dim_device, dim_date
                     facts/  fct_usage, fct_support_tickets
                        -> semantic_models/  (MetricFlow: churn_rate, arpu,
                                               avg_usage_per_subscriber)
```

The raw vault and the Kimball marts are deliberately separate layers: the vault
decouples ingestion from reporting, so a schema change only has to touch a
satellite and a downstream mart, not a full rebuild. See "Proving the
decoupling" below once that demonstration is built.

## Build status

Building step by step, in this order:

1. **Environment & Snowflake connection** -- Python 3.12 venv (kept separate
   from the system's Python 3.14 for `dbt-snowflake` compatibility), dbt-core +
   dbt-snowflake, password passed via `SNOWFLAKE_PASSWORD` env var rather than
   committed to `profiles.yml`. *Done.*
2. **Synthetic data generation** -- `generate_data/generate_signal_data.py`,
   Faker + weighted randomness (skewed plan popularity, realistic device brand
   mix), ~5,000 subscribers and ~195,000 usage events. *Done.*
3. **Raw load** -- `load_to_snowflake.py`, bulk-loaded via `write_pandas` into
   `SIGNAL_DB.RAW`. *Done.*
4. **Staging layer** -- one view per raw source, casting text-typed dates from
   the CSV load into real `DATE`/`TIMESTAMP_NTZ` columns. *Done.*
5. **Raw Vault** -- 4 hubs, 4 links, 7 satellites (expanded from an original
   5-satellite sketch so descriptive attributes never sit directly on a link,
   per strict Data Vault 2.0 discipline), fully tested (`unique`, `not_null`,
   `relationships`) and documented. *Done.*
6. **Kimball marts** -- `dim_subscriber` as a real SCD2 (one row per plan
   segment, not per subscriber), `dim_plan`, `dim_device`, a generated
   `dim_date`, and `fct_usage` / `fct_support_tickets` joined to the correct
   subscriber version via a date-range SCD2 lookup. Fully tested. *Done.*
7. **dbt Semantic Layer** -- `sm_subscriber` and `sm_usage` semantic models,
   `churn_rate` / `arpu` / `avg_usage_per_subscriber` as ratio metrics on top
   of simpler building-block metrics, queried locally with the `mf` CLI.
   *Done.*
8. **dbt contracts + CI proof** -- enforce a contract on at least one model,
   then deliberately break its schema and prove GitHub Actions CI catches it
   rather than silently passing. *In progress.*
9. **GitHub Actions CI/CD** -- automated `dbt build` on every push/PR. *Not started.*
10. **`dbt_project_evaluator`** -- run against the whole project, fix
    everything it flags (undocumented models, missing PK tests, orphaned
    models). *Not started.*
11. **Proving the decoupling** -- add a real new plan attribute and show it
    only touches a satellite and a downstream mart, not a full rebuild.
    *Not started.*
12. **Final polish** -- commit history cleanup, demo, screenshots, CV/portfolio
    link. *Not started.*

## Why Data Vault 2.0 *and* Kimball, not just one

Most portfolios show Kimball alone. Data Vault 2.0 is a well-known enterprise
pattern that fewer candidates can actually speak to hands-on -- hubs (bare
business keys), links (pure relationships, no descriptive attributes), and
satellites (descriptive attributes + full history, one new row per change) are
built specifically to survive schema change without a full rebuild. Kimball's
star schema on top is built for the opposite goal: fast, easy-to-query,
business-friendly tables. Using both in one project, each for what it's
actually good at, is the point -- not a stylistic choice.

## The SCD2 fact join: a real, general technique

`dim_subscriber` has multiple rows per subscriber (one per plan segment,
tracking plan tier and status over time via `valid_from`/`valid_to`). Joining
`fct_usage`/`fct_support_tickets` to the *correct* version isn't a simple key
match -- it's a date-range join:

```sql
on sl.subscriber_id = ds.subscriber_id
and usage.event_timestamp::date >= ds.valid_from
and (ds.valid_to is null or usage.event_timestamp::date < ds.valid_to)
```

`valid_to` is treated as an exclusive boundary on purpose: an event on the
exact day a subscriber switched plans belongs to the new segment, not the old
one. Without that, a boundary-date event would match two dimension rows and
silently duplicate the fact row.

## Known limitation: `churn_rate` is cohort-based, not point-in-time

Querying `churn_rate` grouped by `metric_time__month` answers "of subscribers
whose *current* plan segment started in this month, what fraction eventually
churned" -- because `metric_time` maps to `valid_from`, the date a segment
*started*, not a calendar snapshot of who churned during that specific month.
Both are legitimate, real metrics; they answer different questions. A true
point-in-time version needs a periodic snapshot fact (one row per subscriber
per month, independent of segment boundaries) -- a deliberately deferred,
harder modeling problem, not an oversight.

## Known limitation: two SCD2 mechanisms, and this project only uses one

`dim_subscriber`'s history was reshaped from source data that was *already*
fully historized (`subscription_history` was generated with explicit
start/end dates from the start) -- a single deterministic `SELECT`, not
change detection. A `dbt snapshot` solves the opposite, more common real-world
case: a source that only ever shows current state (an in-place `UPDATE`
overwrites the old value), where dbt has to build history by observing change
across repeated runs. This project demonstrates modeling and querying SCD2
data correctly; it does not yet demonstrate dbt constructing that history
itself via `snapshot`.

---

Screenshots and a full "pipeline in action" walkthrough will be added once the
remaining steps above are complete, in the same style as this portfolio's
other featured projects.
