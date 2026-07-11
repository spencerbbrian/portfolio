-- fct_transactions.sql
--
-- The main fact table. One row per transaction, fully enriched.
-- This is what a BI tool or analyst would query for ad-hoc analysis.
--
-- Column ordering follows a standard convention:
--   1. Keys and identifiers
--   2. Timestamps and dates
--   3. Dimensions (who, what, where)
--   4. Measures (how much)
--   5. Risk and scoring fields

with transactions as (

    select * from {{ ref('int_transactions_enriched') }}

)

select
    -- keys
    transaction_id,
    company_id,
    vendor_id,

    -- time
    transacted_at,
    transaction_date,
    transaction_hour,
    day_of_week,

    -- company dimensions
    company_name,
    company_size_tier,
    baseline_monthly_spend,

    -- vendor dimensions
    vendor_name,
    vendor_category,
    vendor_risk_tier,

    -- transaction dimensions
    department,
    payment_method,
    currency,

    -- measures
    amount_usd,
    amount_to_baseline_ratio,

    -- risk scoring
    risk_tier,
    final_risk_score,
    ml_anomaly_score,
    rule_flag_count,
    risk_flag,

    -- individual rule flags (useful for explainability)
    rule_spend_spike,
    rule_high_risk_vendor,
    rule_off_hours,
    rule_round_amount,
    any_rule_triggered,

    -- simulation ground truth (useful for model evaluation)
    is_simulated_anomaly,
    simulated_anomaly_type

from transactions