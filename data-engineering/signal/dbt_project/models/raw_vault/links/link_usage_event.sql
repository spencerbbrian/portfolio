-- Three-way link: a usage event ties a subscriber, a device, AND the plan
-- that was active at that moment together in one relationship record.
select
    {{ dbt_utils.generate_surrogate_key(['usage_event_id']) }} as usage_event_link_key,
    {{ dbt_utils.generate_surrogate_key(['subscriber_id']) }} as subscriber_hub_key,
    {{ dbt_utils.generate_surrogate_key(['device_id']) }} as device_hub_key,
    {{ dbt_utils.generate_surrogate_key(['plan_id']) }} as plan_hub_key,
    usage_event_id,
    subscriber_id,
    device_id,
    plan_id,
    current_timestamp() as load_date,
    'stg_usage_events' as record_source
from {{ ref('stg_usage_events') }}
