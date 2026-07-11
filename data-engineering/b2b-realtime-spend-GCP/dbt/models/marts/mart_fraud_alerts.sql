-- mart_fraud_alerts.sql
--
-- Flagged transactions only — this is what the fraud/risk dashboard
-- displays. Kept deliberately narrow: only the columns an analyst
-- needs to investigate an alert, plus a human-readable explanation
-- of why it was flagged.
--
-- The alert_reason field is a practical addition — instead of a
-- fraud analyst having to decode four separate boolean columns,
-- they get a plain-English string. In a real system this might
-- also trigger a Slack notification or feed an alerting tool.

with flagged as (

    select * from {{ ref('fct_transactions') }}
    where risk_flag = true

),

with_reason as (

    select
        transaction_id,
        transacted_at,
        company_id,
        company_name,
        company_size_tier,
        vendor_name,
        vendor_category,
        vendor_risk_tier,
        department,
        amount_usd,
        baseline_monthly_spend,
        amount_to_baseline_ratio,

        final_risk_score,
        ml_anomaly_score,
        risk_tier,

        -- Plain-English reason for the flag. Multiple rules can fire
        -- on one transaction — we concatenate them all.
        trim(
            concat(
                if(rule_spend_spike,       'spend spike; ', ''),
                if(rule_high_risk_vendor,  'high-risk vendor; ', ''),
                if(rule_off_hours,         'off-hours transaction; ', ''),
                if(rule_round_amount,      'suspiciously round amount; ', ''),
                if(
                    ml_anomaly_score > 0.4
                    and not any_rule_triggered,
                    'ML anomaly (no rule triggered); ',
                    ''
                )
            )
        )                                       as alert_reason,

        rule_flag_count,
        any_rule_triggered,
        is_simulated_anomaly,
        payment_method

    from flagged

)

select * from with_reason
order by transacted_at desc