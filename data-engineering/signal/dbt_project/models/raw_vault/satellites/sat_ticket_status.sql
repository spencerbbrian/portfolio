-- THE satellite that proves the point of the whole pattern: source data
-- (stg_ticket_status_history) already has one row per status change, so this
-- satellite naturally ends up with multiple rows per ticket_hub_key - one per
-- point in time the status changed. load_date is set to the actual
-- changed_at timestamp (not current_timestamp()) precisely so querying "what
-- was this ticket's status as of a given moment" is a real, answerable
-- question - the audit trail a single overwritten status column could never give you.
select
    {{ dbt_utils.generate_surrogate_key(['ticket_id']) }} as support_ticket_link_key,
    status,
    changed_at as load_date,
    {{ dbt_utils.generate_surrogate_key(['status']) }} as hashdiff,
    'stg_ticket_status_history' as record_source
from {{ ref('stg_ticket_status_history') }}
