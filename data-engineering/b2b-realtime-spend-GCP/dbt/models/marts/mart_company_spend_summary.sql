-- mart_company_spend_summary.sql
--
-- Daily spend summary per company. Powers the "company spend over time"
-- dashboard view and the budget-vs-actual analysis.
--
-- This is intentionally aggregated rather than transaction-grain — a finance
-- team asking "how much did Hernandez LLC spend this week" doesn't need
-- individual transactions, they need daily totals with trend context.

with daily as (

    select * from {{ ref('int_company_daily_spend') }}

),

with_context as (

    select
        transaction_date,
        company_id,
        company_name,
        company_size_tier,
        baseline_monthly_spend,

        transaction_count,
        distinct_vendor_count,
        distinct_category_count,

        total_amount_usd,
        avg_amount_usd,
        max_amount_usd,

        risk_flagged_count,
        spend_spike_count,
        high_risk_vendor_count,
        off_hours_count,
        known_anomaly_count,

        daily_to_baseline_ratio,

        -- How does today's spend compare to a 7-day rolling average?
        -- Useful for spotting unusual days without needing a threshold.
        avg(total_amount_usd) over (
            partition by company_id
            order by transaction_date
            rows between 6 preceding and current row
        )                                           as rolling_7d_avg_spend,

        -- Flag days where spend was more than 3x the 7-day rolling average.
        -- A simple but effective anomaly signal at the daily level.
        total_amount_usd > 3 * avg(total_amount_usd) over (
            partition by company_id
            order by transaction_date
            rows between 6 preceding and current row
        )                                           as is_unusual_spend_day

    from daily

)

select * from with_context
order by transaction_date desc, total_amount_usd desc