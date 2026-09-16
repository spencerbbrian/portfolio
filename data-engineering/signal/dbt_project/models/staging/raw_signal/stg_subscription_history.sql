select
    subscriber_id,
    plan_id,
    start_date::date               as start_date,
    end_date::date                 as end_date
from {{ source('raw_signal', 'subscription_history') }}
