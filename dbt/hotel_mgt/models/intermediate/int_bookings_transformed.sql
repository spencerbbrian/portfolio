-- models/intermediate/int_bookings_transformed.sql
{{ config(materialized='table') }}

with bookings as (
    SELECT
        hotel_id,
        hotel,
        CASE WHEN is_canceled = 1
            THEN 'TRUE'
            ELSE 'FALSE'
        END AS is_canceled,
        lead_time AS leadtime_days,
        PARSE_DATE('%Y-%B-%e',CONCAT(arrival_date_year,'-',arrival_date_month,'-',arrival_date_day_of_month))AS arrival_date,
        arrival_date_week_number,
        stays_in_weekend_nights,
        stays_in_week_nights,
        stays_in_weekend_nights + stays_in_week_nights AS total_stay_nights,
        adults,
        children,
        babies,
        CASE WHEN children > 0 OR babies > 0
            THEN 'TRUE'
            ELSE 'FALSE'
        END AS is_family_booking,
        meal AS meal_package,
        market_segment,
        distribution_channel,
        CASE WHEN is_repeated_guest = 1
            THEN 'TRUE'
            ELSE 'FALSE'
        END AS is_repeated_guest,
        previous_cancellations,
        previous_bookings_not_canceled,
        reserved_room_type,
        assigned_room_type,
        booking_changes,
        deposit_type,
        agent,
        company,
        days_in_waiting_list,
        customer_type,
        adr AS average_daily_rate,
        required_car_parking_spaces,
        total_of_special_requests,
        reservation_status,
        reservation_status_date as reservation_status_update_date
    FROM {{ ref('stg_bookings') }}
    WHERE hotel IN ('Resort Hotel', 'City Hotel')
),

bookings_with_revenue AS (
    SELECT 
        *,
        average_daily_rate * total_stay_nights AS estimated_revenue 
    FROM bookings
)

SELECT *
FROM bookings_with_revenue