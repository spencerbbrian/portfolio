with customers as (

    select * from {{ ref('stg_customers') }}

),

billing_features as (

    select * from {{ ref('int_customer_billing_features') }}

)

select
    c.customer_id,
    c.company_name,
    c.industry,
    c.plan_tier,
    c.employee_count_band,
    c.country,
    c.signup_at,
    c.mrr,
    c.status,
    date_diff(current_date(), date(c.signup_at), day) as tenure_days,
    coalesce(b.payment_failures, 0) as payment_failures,
    coalesce(b.upgrades, 0) as upgrades,
    coalesce(b.downgrades, 0) as downgrades,
    b.canceled_at
from customers c
left join billing_features b on c.customer_id = b.customer_id
