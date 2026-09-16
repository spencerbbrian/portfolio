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
decoupling" below for a real, concrete demonstration of that.

## Build status

Built step by step, in this order:

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
   the CSV load into real `DATE`/`TIMESTAMP_NTZ` columns, organized under
   `models/staging/raw_signal/` (one subfolder per source). *Done.*
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
8. **dbt contracts + CI proof** -- `fct_usage` runs under an enforced contract
   (every column's name and type is a promise, checked on every run); a
   deliberate break (renaming a column in the model while leaving the
   contract unchanged) was pushed on its own branch and confirmed to fail CI
   with a precise column-mismatch error, not a generic SQL error. *Done.*
9. **GitHub Actions CI/CD** -- `dbt build` runs automatically on every
   push/PR that touches the project, using GitHub Actions secrets for the
   Snowflake connection. *Done.*
10. **`dbt_project_evaluator`** -- ran against the whole project; fixed every
    real gap it found (missing descriptions and primary-key tests on all 7
    staging models, a folder-structure mismatch), and recorded the two
    Data-Vault-specific false positives its Kimball-only defaults can't
    recognize (hub/link/satellite naming, `dim_date` as an intentional
    generated root model) as documented exceptions rather than silencing
    them quietly. All checks now pass. *Done.*
11. **Proving the decoupling** -- added `network_generation` (4G/5G) to
    plans, simulating a source system change after the initial build. See
    below for exactly what did and didn't change. *Done.*
12. **Final polish** -- commit history, this README, screenshots. *In
    progress.*

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

## dbt contracts + CI: catching a broken schema before it ships

`fct_usage` is the most-referenced model in the project (used by two semantic
models and the metrics built on top of them), so it's the one where a silent
schema break would actually hurt -- which made it the honest choice to
protect with an enforced contract. A contract declares every column's name
and exact data type up front; dbt checks the model's real output against that
declaration on every run, and refuses to build if they disagree.

To prove this isn't just configuration that looks right, a column was
deliberately renamed in the model's `SELECT` (`sms_count` -> `sms_total`)
without touching the contract, on its own branch, and pushed. CI caught it
immediately with a precise diff, not a vague failure:

```
| column_name | definition_type | contract_type | mismatch_reason       |
| SMS_COUNT   |                  | REAL          | missing in definition |
| SMS_TOTAL   | REAL             |                | missing in contract   |
```

That table is dbt's own contract-check macro, not a custom test -- it's
telling you exactly which column the contract expected that never showed up,
and exactly which column showed up that was never promised.

## `dbt_project_evaluator`: auditing the whole project

`dbt_project_evaluator` is a dbt package that audits a project's structure
against community best practices -- missing descriptions, missing
primary-key tests, folder-naming conventions, orphaned models -- without
touching any data. Running it against Signal surfaced real, fixable gaps
(all 7 staging models had no descriptions or primary-key tests, and the
staging folder didn't follow the evaluator's expected one-subfolder-per-source
layout), all fixed.

It also flagged two things that aren't actually problems here: `hub_`/
`link_`/`sat_` model names (the evaluator only knows Kimball-style prefixes
out of the box, so it has no way to recognize Data Vault naming), and
`dim_date` as a "root model with no parents" (it's intentionally built from
`dbt_utils.date_spine()` alone, a standard pattern for generated date
dimensions). Rather than silencing these, they're recorded as documented
exceptions in `seeds/dbt_project_evaluator_exceptions.csv`, with a real
explanation for each -- visible evidence of understanding *why* a warning
doesn't apply, not just switching it off.

## Proving the decoupling

The vault's whole justification is that ingestion and reporting are
decoupled -- a new descriptive attribute should only ever touch a satellite
and a downstream mart, never a hub, a link, or anything unrelated. To prove
that concretely rather than just asserting it, `network_generation` (`4G` /
`5G`) was added to plans, simulating a source system change after the
project's first build.

The change touched exactly three models: `stg_plans` (pass the new raw
column through), `sat_plan_details` (the satellite that owns plan
attributes -- also folded into its hashdiff, so a future 4G-to-5G change
would register as real history), and `dim_plan` (surface it to reporting).
`hub_plan` and `link_subscription` were untouched, exactly as the theory
predicts: a hub is a pure business key and a link is a pure relationship,
neither should ever need to change for a new descriptive attribute.

`dbt build --select stg_plans sat_plan_details dim_plan` built cleanly
without touching any other model in the project -- including `fct_usage`,
whose `relationships` test against `dim_plan` re-ran and passed without
`fct_usage` itself being rebuilt, confirming the mart's actual data didn't
need to move either.

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

## Pipeline in action

1. **Warehouse layers** -- `SIGNAL_DB` in Snowsight, showing the raw landing
   zone, staging, raw vault, and marts as physically separate schemas.
   ![Snowsight schemas](docs/screenshots/snowsight-schemas.png)

2. **A full build, passing** -- `dbt build` running every model and test in
   the project end to end.
   ![dbt build passing](docs/screenshots/dbt-build-passing.png)

3. **The dependency graph** -- `dbt docs`' lineage view, sources through
   staging, the vault, the marts, and out to the semantic layer.
   ![dbt docs lineage graph](docs/screenshots/dbt-docs-lineage.png)

4. **The database schema** -- an ER diagram generated by `dbterd` straight
   from the project's own `relationships` tests, not hand-drawn.
   ![Signal ER diagram](docs/screenshots/schema-erd.png)

5. **Querying a metric through the semantic layer** -- `churn_rate` returned
   by the `mf` CLI, defined once and available everywhere.
   ![mf query churn_rate](docs/screenshots/mf-query-churn-rate.png)

6. **CI, passing** -- the GitHub Actions baseline run on correct code.
   ![CI passing](docs/screenshots/ci-pass.png)

7. **CI, catching a broken contract** -- the same workflow failing loudly on
   a deliberately broken `fct_usage`, with dbt's own column-mismatch table
   in the log.
   ![CI catching a broken contract](docs/screenshots/ci-contract-fail.png)

8. **A clean project audit** -- `dbt_project_evaluator` passing with zero
   warnings after fixing every real gap it found.
   ![dbt_project_evaluator clean run](docs/screenshots/dbt-project-evaluator-clean.png)

9. **The decoupling, as a diff** -- the file list from adding
   `network_generation`, contained to exactly the models the theory
   predicts.
   ![Decoupling proof diff](docs/screenshots/decoupling-diff.png)
