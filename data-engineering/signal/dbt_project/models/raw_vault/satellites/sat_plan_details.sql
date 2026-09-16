select
    {{ dbt_utils.generate_surrogate_key(['plan_id']) }} as plan_hub_key,
    plan_name,
    plan_type,
    data_allowance_gb,
    voice_minutes,
    sms_allowance,
    monthly_price,
    network_generation,
    current_timestamp() as load_date,
    {{ dbt_utils.generate_surrogate_key(['plan_name', 'plan_type', 'data_allowance_gb', 'voice_minutes', 'sms_allowance', 'monthly_price', 'network_generation']) }} as hashdiff,
    'stg_plans' as record_source
from {{ ref('stg_plans') }}
