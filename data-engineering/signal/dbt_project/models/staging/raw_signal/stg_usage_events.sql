select
    usage_event_id,
    subscriber_id,
    device_id,
    plan_id,
    event_type,
    -- ISO timestamp string -> real TIMESTAMP_NTZ (NTZ = "no time zone",
    -- fine here since this is synthetic data with no real timezone meaning)
    event_timestamp::timestamp_ntz as event_timestamp,
    data_used_mb,
    call_duration_seconds,
    sms_count
from {{ source('raw_signal', 'usage_events') }}
