-- Required scaffolding for the dbt Semantic Layer / MetricFlow - not
-- something specific to this project. MetricFlow needs its own dedicated
-- day-level date spine to do time-based rollups (day -> week -> month ->
-- year) for ANY metric, and it doesn't automatically know dim_date could
-- serve that purpose even though the two look nearly identical - it has to
-- be a model explicitly declared as the time spine (see the yml below).
{{ dbt_utils.date_spine(
    datepart="day",
    start_date="cast('2023-01-01' as date)",
    end_date="cast('2026-09-02' as date)"
) }}
