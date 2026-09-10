select
    ticket_id,
    subscriber_id,
    created_at::timestamp_ntz      as created_at,
    category,
    priority,
    current_status,
    resolved_at::timestamp_ntz     as resolved_at
from {{ source('raw_signal', 'support_tickets') }}
