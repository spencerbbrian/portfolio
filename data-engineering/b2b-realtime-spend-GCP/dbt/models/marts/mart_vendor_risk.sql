-- mart_vendor_risk.sql
--
-- Vendor-level risk summary across all transactions.
-- Answers: which vendors show up disproportionately in flagged transactions?
-- Which vendor categories carry the most risk?
--
-- This is the kind of table a risk team would review weekly to decide
-- whether to blacklist a vendor or add it to a watchlist.
--
-- One row per vendor.

with transactions as (

    select * from {{ ref('fct_transactions') }}

),

vendor_summary as (

    select
        vendor_id,
        vendor_name,
        vendor_category,
        vendor_risk_tier,

        count(*)                                        as total_transactions,
        count(distinct company_id)                      as distinct_companies,

        sum(amount_usd)                                 as total_amount_usd,
        avg(amount_usd)                                 as avg_amount_usd,
        max(amount_usd)                                 as max_amount_usd,

        countif(risk_flag)                              as flagged_transaction_count,
        safe_divide(
            countif(risk_flag),
            count(*)
        )                                               as flag_rate,

        countif(rule_spend_spike)                       as spend_spike_count,
        countif(rule_high_risk_vendor)                  as high_risk_vendor_rule_count,

        -- The average ML anomaly score across all transactions with this vendor.
        -- A consistently high score suggests the vendor itself is unusual,
        -- not just individual transactions.
        avg(ml_anomaly_score)                           as avg_ml_anomaly_score,
        max(final_risk_score)                           as max_risk_score,

        min(transacted_at)                              as first_seen,
        max(transacted_at)                              as last_seen

    from transactions
    group by 1, 2, 3, 4

),

with_risk_label as (

    select
        *,

        -- Overall vendor risk label based on flag rate and vendor_risk_tier.
        -- We combine the static tier (from our reference data) with the
        -- observed flag rate from actual transactions.
        case
            when flag_rate >= 0.3 or vendor_risk_tier = 'high'  then 'high'
            when flag_rate >= 0.1 or vendor_risk_tier = 'medium' then 'medium'
            else 'low'
        end                                             as observed_risk_label

    from vendor_summary

)

select * from with_risk_label
order by flag_rate desc, total_amount_usd desc