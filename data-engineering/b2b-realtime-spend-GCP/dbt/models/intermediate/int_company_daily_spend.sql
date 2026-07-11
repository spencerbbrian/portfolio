-- int_company_daily_spend.sql
--
-- Rolls up transaction-grain data to a daily company-grain summary.
-- The windowed aggregates from the Beam pipeline use 5-minute windows
-- which are too granular for daily trend analysis in the dashboard.
-- This intermediate model bridges that gap.
--
-- Note: we build this from stg_transactions rather than
-- stg_company_spend_windows because the transaction grain lets us
-- accurately count distinct vendors and compute risk metrics that
-- the windowed table doesn't carry.

with transactions as (

    select * from {{ ref('int_transactions_enriched') }}

),

daily as (

    select
        transaction_date,
        company_id,
        company_name,
        company_size_tier,
        baseline_monthly_spend,

        count(*)                                            as transaction_count,
        count(distinct vendor_id)                           as distinct_vendor_count,
        count(distinct vendor_category)                     as distinct_category_count,

        sum(amount_usd)                                     as total_amount_usd,
        avg(amount_usd)                                     as avg_amount_usd,
        max(amount_usd)                                     as max_amount_usd,

        countif(risk_flag)                                  as risk_flagged_count,
        countif(rule_spend_spike)                           as spend_spike_count,
        countif(rule_high_risk_vendor)                      as high_risk_vendor_count,
        countif(rule_off_hours)                             as off_hours_count,
        countif(is_simulated_anomaly)                       as known_anomaly_count,

        -- What fraction of the monthly baseline did this company
        -- spend today? Above 1.0 means they exceeded their monthly
        -- budget in a single day.
        safe_divide(
            sum(amount_usd),
            baseline_monthly_spend
        )                                                   as daily_to_baseline_ratio

    from transactions
    group by 1, 2, 3, 4, 5

)

select * from daily