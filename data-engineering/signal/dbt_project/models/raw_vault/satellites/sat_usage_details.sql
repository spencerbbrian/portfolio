-- This satellite hangs off the LINK (usage_event_link_key), not a hub -
-- because these attributes describe the usage EVENT itself (the
-- relationship instance), not any one of the subscriber/device/plan hubs.
select
    {{ dbt_utils.generate_surrogate_key(['usage_event_id']) }} as usage_event_link_key,
    event_type,
    event_timestamp,
    data_used_mb,
    call_duration_seconds,
    sms_count,
    current_timestamp() as load_date,
    {{ dbt_utils.generate_surrogate_key(['event_type', 'event_timestamp', 'data_used_mb', 'call_duration_seconds', 'sms_count']) }} as hashdiff,
    'stg_usage_events' as record_source
from {{ ref('stg_usage_events') }}
