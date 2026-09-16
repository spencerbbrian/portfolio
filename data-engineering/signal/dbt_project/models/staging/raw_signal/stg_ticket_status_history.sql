select
    ticket_id,
    status,
    changed_at::timestamp_ntz      as changed_at
from {{ source('raw_signal', 'ticket_status_history') }}
