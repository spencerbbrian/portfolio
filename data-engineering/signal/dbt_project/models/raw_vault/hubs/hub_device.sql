select
    {{ dbt_utils.generate_surrogate_key(['device_id']) }} as device_hub_key,
    device_id,
    current_timestamp() as load_date,
    'stg_devices' as record_source
from {{ ref('stg_devices') }}
