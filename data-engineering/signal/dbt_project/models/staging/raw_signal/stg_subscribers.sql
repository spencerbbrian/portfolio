select
    subscriber_id,
    first_name,
    last_name,
    email,
    phone_number,
    -- these landed as plain text strings from the CSV load, so we cast them
    -- into real DATE types here - this is the whole point of a staging layer.
    date_of_birth::date            as date_of_birth,
    signup_date::date              as signup_date,
    status,
    churn_date::date               as churn_date
from {{ source('raw_signal', 'subscribers') }}
