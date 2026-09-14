select
    {{ dbt_utils.generate_surrogate_key(['device_id']) }} as device_hub_key,
    brand,
    model,
    imei,
    device_type,
    current_timestamp() as load_date,
    {{ dbt_utils.generate_surrogate_key(['brand', 'model', 'imei', 'device_type']) }} as hashdiff,
    'stg_devices' as record_source
from {{ ref('stg_devices') }}
