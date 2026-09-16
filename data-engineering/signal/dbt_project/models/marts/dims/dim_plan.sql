-- Simple dimension (no SCD2 needed - plans don't change identity, and we're
-- not tracking plan price history in this project). Just joins the hub to
-- its satellite to combine identity + descriptive attributes into one
-- flat, easy-to-query table - this is the payoff of the vault split.
select
    p.plan_hub_key   as plan_key,
    h.plan_id,
    p.plan_name,
    p.plan_type,
    p.data_allowance_gb,
    p.voice_minutes,
    p.sms_allowance,
    p.monthly_price
from {{ ref('hub_plan') }} h
inner join {{ ref('sat_plan_details') }} p
    on h.plan_hub_key = p.plan_hub_key
