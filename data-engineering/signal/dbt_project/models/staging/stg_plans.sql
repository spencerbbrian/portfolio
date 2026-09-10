-- Plans is pure reference data - no dates to cast, just passed through cleanly.
select
    plan_id,
    plan_name,
    plan_type,
    data_allowance_gb,
    voice_minutes,
    sms_allowance,
    monthly_price
from {{ source('raw_signal', 'plans') }}
