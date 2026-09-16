-- Also added beyond the original sketch: category/priority/current_status/
-- resolved_at are descriptive attributes of the ticket relationship, so they
-- get their own satellite rather than living on link_support_ticket.
-- current_status here is the ticket's LATEST status as a convenience column;
-- sat_ticket_status above is still the source of truth for the full history.
select
    {{ dbt_utils.generate_surrogate_key(['ticket_id']) }} as support_ticket_link_key,
    category,
    priority,
    current_status,
    created_at,
    resolved_at,
    current_timestamp() as load_date,
    {{ dbt_utils.generate_surrogate_key(['category', 'priority', 'current_status', 'resolved_at']) }} as hashdiff,
    'stg_support_tickets' as record_source
from {{ ref('stg_support_tickets') }}
