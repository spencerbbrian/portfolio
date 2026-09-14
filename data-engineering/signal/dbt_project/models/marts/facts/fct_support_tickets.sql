-- Grain: one row per support ticket.
with tickets as (

    select
        lt.ticket_id,
        lt.subscriber_hub_key,
        td.category,
        td.priority,
        td.current_status,
        td.created_at,
        td.resolved_at
    from {{ ref('link_support_ticket') }} lt
    inner join {{ ref('sat_ticket_details') }} td
        on lt.support_ticket_link_key = td.support_ticket_link_key

),

subscriber_lookup as (
    select subscriber_hub_key, subscriber_id
    from {{ ref('hub_subscriber') }}
)

select
    tickets.ticket_id,
    ds.subscriber_key,
    to_number(to_char(tickets.created_at::date, 'YYYYMMDD')) as date_key,
    tickets.category,
    tickets.priority,
    tickets.current_status,
    tickets.created_at,
    tickets.resolved_at,
    -- a genuinely useful derived metric, not just a passthrough column:
    -- how many hours the ticket took to resolve. Null if still unresolved.
    datediff('hour', tickets.created_at, tickets.resolved_at) as resolution_hours
from tickets
inner join subscriber_lookup sl
    on tickets.subscriber_hub_key = sl.subscriber_hub_key
inner join {{ ref('dim_subscriber') }} ds
    on sl.subscriber_id = ds.subscriber_id
    and tickets.created_at::date >= ds.valid_from
    and (ds.valid_to is null or tickets.created_at::date < ds.valid_to)
