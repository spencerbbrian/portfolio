{{
    config(
        materialized='table',
    )
}}

-- Required by the dbt Semantic Layer / MetricFlow: a single-column table of
-- every calendar day, used internally to resolve time-based metric queries
-- (e.g. `--group-by metric_time__month`) at any granularity, regardless of
-- what granularity the underlying fact tables are recorded at.
--
-- Generated natively with Snowflake's GENERATOR/SEQ4 rather than pulling in
-- the dbt_utils package just for its date_spine macro.

with days as (
    select
        dateadd(day, seq4(), '2000-01-01'::date) as date_day
    from table(generator(rowcount => 12000))  -- 2000-01-01 through ~2032: comfortable headroom around the Olist dataset's actual date range
)

select date_day
from days
