select
    {{ dbt_utils.generate_surrogate_key(['subscriber_id', 'device_id']) }} as subscriber_device_link_key,
    {{ dbt_utils.generate_surrogate_key(['subscriber_id']) }} as subscriber_hub_key,
    {{ dbt_utils.generate_surrogate_key(['device_id']) }} as device_hub_key,
    subscriber_id,
    device_id,
    current_timestamp() as load_date,
    'stg_devices' as record_source
from {{ ref('stg_devices') }}
