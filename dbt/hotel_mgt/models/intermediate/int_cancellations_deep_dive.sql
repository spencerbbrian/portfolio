{{ config(materialized='table') }}

WITH source AS (
    SELECT
        hotel_id,
        hotel,
        is_canceled,
        leadtime_days,
        arrival_date,
        reservation_status,
        reservation_status_update_date,
        deposit_type,
        average_daily_rate,
        total_stay_nights,
        estimated_revenue,
        market_segment,
        distribution_channel,
        customer_type,
        reserved_room_type,
        assigned_room_type,
        previous_cancellations
    FROM {{ ref('int_bookings_transformed') }}
),

enriched AS (
    SELECT
        *,

        -- Booking date derived by subtracting lead time from arrival date
        DATE_SUB(arrival_date, INTERVAL leadtime_days DAY)             AS booking_date,

        -- Days between cancellation date and booking date
        CASE
            WHEN is_canceled = 'TRUE'
            THEN DATE_DIFF(
                reservation_status_update_date,
                DATE_SUB(arrival_date, INTERVAL leadtime_days DAY),
                DAY
            )
            ELSE NULL
        END                                                             AS days_to_cancellation,

        -- Days remaining before arrival when cancellation happened
        CASE
            WHEN is_canceled = 'TRUE'
            THEN DATE_DIFF(arrival_date, reservation_status_update_date, DAY)
            ELSE NULL
        END                                                             AS days_before_arrival_at_cancellation,

        -- Late cancellation: canceled less than 7 days before arrival
        CASE
            WHEN is_canceled = 'TRUE'
                AND DATE_DIFF(arrival_date, reservation_status_update_date, DAY) < 7
            THEN TRUE
            ELSE FALSE
        END                                                             AS is_late_cancellation,

        -- Deposit type vs cancellation outcome
        CONCAT(
            CASE WHEN is_canceled = 'TRUE' THEN 'Canceled' ELSE 'Retained' END,
            ' - ',
            COALESCE(deposit_type, 'No Deposit')
        )AS deposit_cancellation_outcome,

        -- Revenue lost only on canceled bookings
        CASE
            WHEN is_canceled = 'TRUE' THEN estimated_revenue
            ELSE 0
        END                                                             AS revenue_lost

    FROM source
)

SELECT * FROM enriched