select
    {{ dbt_utils.generate_surrogate_key(['plan_id']) }} as plan_hub_key,
    plan_id,
    current_timestamp() as load_date,
    'stg_plans' as record_source
from {{ ref('stg_plans') }}
