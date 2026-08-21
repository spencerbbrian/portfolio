with usage as (

    select * from {{ ref('stg_usage_events') }}

),

logins as (

    select
        customer_id,
        count(*) as total_logins,
        countif(event_at >= timestamp_sub(current_timestamp(), interval 30 day)) as logins_last_30d,
        countif(event_at >= timestamp_sub(current_timestamp(), interval 60 day)) as logins_last_60d,
        max(event_at) as last_login_at
    from usage
    where event_type = 'login'
    group by customer_id

),

feature_usage as (

    select
        customer_id,
        count(distinct feature_name) as distinct_features_used,
        count(*) as total_feature_events
    from usage
    where event_type = 'feature_used'
    group by customer_id

)

select
    coalesce(l.customer_id, f.customer_id) as customer_id,
    coalesce(l.total_logins, 0) as total_logins,
    coalesce(l.logins_last_30d, 0) as logins_last_30d,
    coalesce(l.logins_last_60d, 0) as logins_last_60d,
    l.last_login_at,
    timestamp_diff(current_timestamp(), l.last_login_at, day) as days_since_last_login,
    coalesce(f.distinct_features_used, 0) as distinct_features_used,
    coalesce(f.total_feature_events, 0) as total_feature_events
from logins l
full outer join feature_usage f on l.customer_id = f.customer_id
