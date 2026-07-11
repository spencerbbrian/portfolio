with source as (

    select * from {{ source('raw', 'transactions_scored') }}

),

cleaned as (

    select
        -- identifiers
        transaction_id,
        company_id,
        vendor_id,

        -- company context
        company_name,
        company_size_tier,
        cast(baseline_monthly_spend as numeric)     as baseline_monthly_spend,

        -- vendor context
        vendor_name,
        vendor_category,
        vendor_risk_tier,

        -- transaction facts
        cast(amount_usd as numeric)                 as amount_usd,
        currency,
        payment_method,
        department,
        parse_timestamp('%Y-%m-%dT%H:%M:%E*S%Ez', timestamp) as transacted_at,

        -- producer anomaly label (ground truth from simulation)
        coalesce(is_anomaly, false)                 as is_simulated_anomaly,
        anomaly_type                                as simulated_anomaly_type,

        -- rule flags
        coalesce(rule_spend_spike, false)           as rule_spend_spike,
        coalesce(rule_high_risk_vendor, false)      as rule_high_risk_vendor,
        coalesce(rule_off_hours, false)             as rule_off_hours,
        coalesce(rule_round_amount, false)          as rule_round_amount,
        coalesce(rule_flag_count, 0)                as rule_flag_count,
        coalesce(any_rule_triggered, false)         as any_rule_triggered,

        -- ml scores
        ml_raw_score,
        cast(ml_anomaly_score as numeric)           as ml_anomaly_score,
        cast(rule_contribution as numeric)          as rule_contribution,
        cast(final_risk_score as numeric)           as final_risk_score,
        coalesce(risk_flag, false)                  as risk_flag

    from source
    where transaction_id is not null

)

select * from cleaned