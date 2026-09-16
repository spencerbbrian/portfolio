-- A standard Kimball date dimension - one row per calendar day, generated
-- from scratch (not from any source table) using dbt_utils' date_spine.
-- date_key is an integer YYYYMMDD, the conventional Kimball surrogate key
-- for a date dimension (sorts and joins cheaply, and is human-readable
-- when you glance at raw fact table data).
with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2023-01-01' as date)",
        end_date="cast('2026-09-02' as date)"
    ) }}
)

select
    to_number(to_char(date_day, 'YYYYMMDD')) as date_key,
    date_day,
    year(date_day)          as year,
    month(date_day)         as month,
    day(date_day)           as day_of_month,
    dayofweekiso(date_day)  as day_of_week,   -- 1 = Monday ... 7 = Sunday
    dayname(date_day)       as day_name,
    case when dayofweekiso(date_day) in (6, 7) then true else false end as is_weekend
from spine
