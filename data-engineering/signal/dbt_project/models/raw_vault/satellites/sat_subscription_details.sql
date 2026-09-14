-- Added beyond the original 5-satellite sketch: end_date is a descriptive,
-- changeable attribute of the subscription relationship (it gets filled in
-- later when a subscriber switches plans), so strict Data Vault says it
-- belongs in a satellite off link_subscription, not sitting directly on the link.
select
    {{ dbt_utils.generate_surrogate_key(['subscriber_id', 'plan_id', 'start_date']) }} as subscription_link_key,
    start_date,
    end_date,
    current_timestamp() as load_date,
    {{ dbt_utils.generate_surrogate_key(['end_date']) }} as hashdiff,
    'stg_subscription_history' as record_source
from {{ ref('stg_subscription_history') }}
