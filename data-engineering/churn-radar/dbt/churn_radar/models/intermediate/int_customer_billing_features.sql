with billing as (

    select * from {{ ref('stg_billing_events') }}

),

billing_features as (

    select
        customer_id,
        countif(event_type = 'payment_failed') as payment_failures,
        countif(event_type = 'plan_upgraded') as upgrades,
        countif(event_type = 'plan_downgraded') as downgrades,
        max(if(event_type = 'subscription_canceled', event_at, null)) as canceled_at
    from billing
    group by customer_id

)

select * from billing_features
