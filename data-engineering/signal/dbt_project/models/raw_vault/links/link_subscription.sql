-- Links subscriber <-> plan. start_date is part of the link's own business
-- key (not a descriptive attribute) because it's what makes each plan-change
-- segment a distinct relationship instance - without it, a subscriber who
-- went Basic -> Unlimited -> Basic again would collapse into one row.
select
    {{ dbt_utils.generate_surrogate_key(['subscriber_id', 'plan_id', 'start_date']) }} as subscription_link_key,
    {{ dbt_utils.generate_surrogate_key(['subscriber_id']) }} as subscriber_hub_key,
    {{ dbt_utils.generate_surrogate_key(['plan_id']) }} as plan_hub_key,
    subscriber_id,
    plan_id,
    start_date,
    current_timestamp() as load_date,
    'stg_subscription_history' as record_source
from {{ ref('stg_subscription_history') }}
