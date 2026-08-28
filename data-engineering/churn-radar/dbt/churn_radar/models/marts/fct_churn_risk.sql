with customers as (

    select * from {{ ref('dim_customers') }}

),

engagement as (

    select * from {{ ref('int_customer_engagement_features') }}

),

tickets as (

    select * from {{ ref('int_support_ticket_features') }}

),

scored as (

    select
        c.customer_id,
        c.company_name,
        c.industry,
        c.plan_tier,
        c.mrr,
        c.status,
        c.tenure_days,
        coalesce(e.logins_last_30d, 0) as logins_last_30d,
        e.days_since_last_login,
        coalesce(e.distinct_features_used, 0) as distinct_features_used,
        coalesce(t.open_tickets, 0) as open_tickets,
        c.payment_failures,
        c.downgrades,
        c.upgrades,
        -- health_score is only meaningful for customers still using the
        -- product -- a canceled customer doesn't need a forward-looking
        -- score, they need a churn_risk_tier of 'Churned' (below).
        case
            when c.status = 'active' then {{ calculate_health_score(
                'coalesce(e.logins_last_30d, 0)',
                'coalesce(e.days_since_last_login, 999)',
                'coalesce(e.distinct_features_used, 0)',
                'coalesce(t.open_tickets, 0)',
                'c.payment_failures',
                'c.downgrades',
                'c.upgrades'
            ) }}
            else null
        end as health_score
    from customers c
    left join engagement e on c.customer_id = e.customer_id
    left join tickets t on c.customer_id = t.customer_id

)

select
    *,
    case
        when status = 'canceled' then 'Churned'
        when health_score >= 75 then 'Low'
        when health_score >= 50 then 'Medium'
        when health_score >= 25 then 'High'
        else 'Critical'
    end as churn_risk_tier
from scored
