with usage as (

    select * from {{ ref('stg_usage_events') }}

),

tickets as (

    select
        customer_id,
        countif(event_type = 'support_ticket_opened') as tickets_opened,
        countif(event_type = 'support_ticket_resolved') as tickets_resolved
    from usage
    where event_type in ('support_ticket_opened', 'support_ticket_resolved')
    group by customer_id

)

select
    customer_id,
    tickets_opened,
    tickets_resolved,
    tickets_opened - tickets_resolved as open_tickets
from tickets
