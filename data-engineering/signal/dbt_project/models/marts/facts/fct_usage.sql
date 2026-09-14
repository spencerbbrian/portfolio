-- Grain: one row per usage event.
with usage as (

    select
        lu.usage_event_id,
        lu.subscriber_hub_key,
        lu.device_hub_key,
        lu.plan_hub_key,
        sd.event_type,
        sd.event_timestamp,
        sd.data_used_mb,
        sd.call_duration_seconds,
        sd.sms_count
    from {{ ref('link_usage_event') }} lu
    inner join {{ ref('sat_usage_details') }} sd
        on lu.usage_event_link_key = sd.usage_event_link_key

),

subscriber_lookup as (
    select subscriber_hub_key, subscriber_id
    from {{ ref('hub_subscriber') }}
)

select
    usage.usage_event_id,
    -- SCD2 lookup: match this event to whichever dim_subscriber row (which
    -- plan segment) was actually valid on the day the event happened.
    -- valid_to is treated as EXCLUSIVE here - an event on the exact day a
    -- subscriber switched plans belongs to the NEW segment, not the old
    -- one, and being consistent about that stops a boundary-date event
    -- from matching two rows and duplicating this fact row.
    ds.subscriber_key,
    usage.device_hub_key   as device_key,
    usage.plan_hub_key     as plan_key,
    to_number(to_char(usage.event_timestamp::date, 'YYYYMMDD')) as date_key,
    usage.event_type,
    usage.event_timestamp,
    usage.data_used_mb,
    usage.call_duration_seconds,
    usage.sms_count
from usage
inner join subscriber_lookup sl
    on usage.subscriber_hub_key = sl.subscriber_hub_key
inner join {{ ref('dim_subscriber') }} ds
    on sl.subscriber_id = ds.subscriber_id
    and usage.event_timestamp::date >= ds.valid_from
    and (ds.valid_to is null or usage.event_timestamp::date < ds.valid_to)
