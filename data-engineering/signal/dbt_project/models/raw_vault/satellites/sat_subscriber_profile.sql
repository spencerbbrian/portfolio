select
    {{ dbt_utils.generate_surrogate_key(['subscriber_id']) }} as subscriber_hub_key,
    first_name,
    last_name,
    email,
    phone_number,
    date_of_birth,
    signup_date,
    status,
    churn_date,
    current_timestamp() as load_date,
    -- hashdiff: a hash of every descriptive column below. On an incremental
    -- run, comparing this run's hashdiff to the last stored one is how you'd
    -- decide "did anything actually change" without comparing column by
    -- column - if it matches, skip the insert; if not, insert a new version.
    {{ dbt_utils.generate_surrogate_key(['first_name', 'last_name', 'email', 'phone_number', 'status', 'churn_date']) }} as hashdiff,
    'stg_subscribers' as record_source
from {{ ref('stg_subscribers') }}
