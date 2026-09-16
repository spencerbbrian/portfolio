select
    {{ dbt_utils.generate_surrogate_key(['ticket_id']) }} as ticket_hub_key,
    ticket_id,
    current_timestamp() as load_date,
    'stg_support_tickets' as record_source
from {{ ref('stg_support_tickets') }}
