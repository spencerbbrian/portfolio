select
    d.device_hub_key   as device_key,
    h.device_id,
    d.brand,
    d.model,
    d.imei,
    d.device_type
from {{ ref('hub_device') }} h
inner join {{ ref('sat_device_details') }} d
    on h.device_hub_key = d.device_hub_key
