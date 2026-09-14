-- The SCD2 dimension - the textbook "subscriber changed tier" case.
-- One row per subscriber PER PLAN SEGMENT, not one row per subscriber.
-- A subscriber who switched plans twice gets 3 rows here, each with its
-- own valid_from/valid_to window and its own subscriber_key.

with segments as (

    -- link_subscription + its satellite together give us: which subscriber,
    -- which plan, and the start/end dates of that specific segment.
    select
        ls.subscriber_hub_key,
        ls.plan_hub_key,
        sd.start_date,
        sd.end_date
    from {{ ref('link_subscription') }} ls
    inner join {{ ref('sat_subscription_details') }} sd
        on ls.subscription_link_key = sd.subscription_link_key

),

profile as (

    -- Subscriber's personal details don't change over time in this project
    -- (no satellite history for them), so this is a single flat lookup.
    select
        h.subscriber_hub_key,
        h.subscriber_id,
        p.first_name,
        p.last_name,
        p.email,
        p.phone_number,
        p.date_of_birth,
        p.signup_date,
        p.status      as overall_status,
        p.churn_date
    from {{ ref('hub_subscriber') }} h
    inner join {{ ref('sat_subscriber_profile') }} p
        on h.subscriber_hub_key = p.subscriber_hub_key

)

select
    -- a NEW surrogate key per segment (not per subscriber) - this is what
    -- makes it SCD2 rather than just a subscriber lookup table.
    {{ dbt_utils.generate_surrogate_key(['profile.subscriber_id', 'segments.start_date']) }} as subscriber_key,
    profile.subscriber_id,
    profile.first_name,
    profile.last_name,
    profile.email,
    profile.phone_number,
    profile.date_of_birth,
    profile.signup_date,
    plan.plan_name    as plan_tier,
    plan.plan_id,
    -- If this segment has an end_date, the subscriber went on to ANOTHER
    -- plan afterwards - so they were still active during this segment no
    -- matter what happened later. Only their very last segment (end_date is
    -- null) can actually show as 'churned', and only if they churned overall.
    case
        when segments.end_date is not null then 'active'
        else profile.overall_status
    end               as status,
    segments.start_date as valid_from,
    segments.end_date   as valid_to,
    case when segments.end_date is null then true else false end as is_current
from segments
inner join profile
    on segments.subscriber_hub_key = profile.subscriber_hub_key
inner join {{ ref('dim_plan') }} plan
    on segments.plan_hub_key = plan.plan_key
