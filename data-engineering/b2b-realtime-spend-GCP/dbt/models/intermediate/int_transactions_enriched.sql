-- int_transactions_enriched.sql
--
-- Adds derived fields that are useful across multiple mart models but don't
-- belong in staging (staging is just cleaning, not business logic).
--
-- Derived fields added here:
--   - risk_tier: human-readable bucketing of the continuous final_risk_score
--   - amount_to_baseline_ratio: how large this transaction is relative to the
--     company's monthly baseline — a $50k transaction is normal for enterprise,
--     alarming for an SMB
--   - transaction_hour / transaction_date / day_of_week: time components for
--     the dashboard's time-of-day analysis
--   - is_off_hours: mirrors the rule logic, useful for dashboard filtering
--     without needing to expose the raw rule flag name

with transactions as (

    select * from {{ ref('stg_transactions') }}

),

enriched as (

    select
        *,

        -- Risk bucketing — easier to filter/display in a dashboard than
        -- a raw 0-1 score. Thresholds are deliberate:
        --   high:   anything that triggered risk_flag (score >= 0.5)
        --   medium: elevated but not flagged (0.3–0.5, worth watching)
        --   low:    everything else
        case
            when final_risk_score >= 0.75 then 'high'
            when final_risk_score >= 0.4 then 'medium'
            else 'low'
        end                                                 as risk_tier,

        -- How large is this transaction relative to what we'd expect?
        -- 1.0 = equal to the company's full monthly baseline (very suspicious)
        -- 0.01 = 1% of monthly baseline (typical single transaction)
        safe_divide(amount_usd, baseline_monthly_spend)     as amount_to_baseline_ratio,

        -- Time components for dashboards
        extract(hour from transacted_at)                    as transaction_hour,
        date(transacted_at)                                 as transaction_date,
        format_timestamp('%A', transacted_at)               as day_of_week,

        -- Off-hours flag — matches the rule in rules.py
        extract(hour from transacted_at) between 0 and 4   as is_off_hours

    from transactions

)

select * from enriched