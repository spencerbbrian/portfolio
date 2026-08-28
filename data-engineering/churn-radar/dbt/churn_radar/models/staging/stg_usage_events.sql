with usage_events as (

    select
        event_id,
        customer_id,
        cast(event_timestamp as timestamp) as event_at,
        event_type,
        feature_name,
        session_duration_seconds,
        user_email,
        cast(created_at as timestamp) as created_at
    from {{ source('churn_radar', 'usage_events') }}

)

select * from usage_events
