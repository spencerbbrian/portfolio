-- Hub: pure business key + hash key. No descriptive attributes ever - that's
-- the whole discipline of a hub. subscriber_hub_key is what links/satellites
-- reference instead of the raw business key, so if the business key's format
-- ever changed upstream, only this one hub would need to change.
select
    {{ dbt_utils.generate_surrogate_key(['subscriber_id']) }} as subscriber_hub_key,
    subscriber_id,
    current_timestamp() as load_date,
    'stg_subscribers' as record_source
from {{ ref('stg_subscribers') }}
