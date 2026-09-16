select
    device_id,
    subscriber_id,
    brand,
    model,
    imei,
    device_type
from {{ source('raw_signal', 'devices') }}
