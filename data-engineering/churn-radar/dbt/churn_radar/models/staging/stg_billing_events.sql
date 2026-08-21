with billing_events as (

    select
        event_id,
        customer_id,
        cast(event_timestamp as timestamp) as event_at,
        event_type,
        mrr_before,
        mrr_after,
        plan_tier,
        cast(created_at as timestamp) as created_at
    from {{ source('churn_radar', 'billing_events') }}

)

select * from billing_events
