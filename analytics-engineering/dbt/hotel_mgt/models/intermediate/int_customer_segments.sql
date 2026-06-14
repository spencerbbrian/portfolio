{{ config(materialized='table') }}

WITH customer_data AS (
    SELECT
        row_number() over () AS customer_id,
        leadtime_days,
        total_stay_nights,
        is_repeated_guest,
        previous_cancellations,
        reserved_room_type,
        average_daily_rate,
        reservation_status,
        estimated_revenue
    FROM {{ ref('int_bookings_transformed') }}
),

customer_classification AS (
    SELECT
        customer_id,
        leadtime_days,
        total_stay_nights,
        previous_cancellations,
        reserved_room_type,
        average_daily_rate,
        estimated_revenue,
        CASE
            WHEN leadtime_days < 30 AND total_stay_nights < 3 AND is_repeated_guest = 'FALSE' THEN 'New'
            WHEN leadtime_days >= 30 AND total_stay_nights >= 3 AND is_repeated_guest = 'TRUE' THEN 'Loyal'
            ELSE 'Occasional'
        END AS customer_segment,
        CASE 
            WHEN total_stay_nights >= 50 THEN 100
            WHEN total_stay_nights >= 20 THEN 50
            WHEN total_stay_nights >= 10 THEN 20
            WHEN total_stay_nights >= 5 THEN 10
            ELSE 0
        END AS stay_loyalty_points,
        CASE
            WHEN is_repeated_guest = 'TRUE' THEN 100
            ELSE 0
        END AS repeat_customer_points,
        CASE
            WHEN previous_cancellations > 0 THEN -50
            ELSE 0
        END AS cancellation_penalty_points,
        CASE
            WHEN reserved_room_type IN ('A') THEN 500
            WHEN reserved_room_type IN ('B', 'C') THEN 250
            WHEN reserved_room_type IN ('D', 'E', 'F') THEN 200
            WHEN reserved_room_type IN ('G', 'H') THEN 100
            ELSE 0
        END AS room_type_points,
        CASE
            WHEN average_daily_rate >= 2500 THEN 2500
            WHEN average_daily_rate >= 1000 THEN 1000
            WHEN average_daily_rate >= 500 THEN 750
            WHEN average_daily_rate >= 100 THEN 210
            WHEN average_daily_rate >= 50 THEN 10
            ELSE 0
        END AS spending_points,
        CASE
            WHEN reservation_status = 'Canceled' THEN -250
            WHEN reservation_status = 'Check-Out' THEN 100
            WHEN reservation_status = 'No-Show' THEN -50
            ELSE 0
        END AS reservation_status_points,
        CASE
            WHEN estimated_revenue >= 5000 THEN 3000
            WHEN estimated_revenue >= 3500 THEN 2000
            WHEN estimated_revenue >= 3000 THEN 1800
            WHEN estimated_revenue >= 2500 THEN 1500
            WHEN estimated_revenue >= 1000 THEN 1000
            WHEN estimated_revenue >= 500 THEN 750
            WHEN estimated_revenue >= 250 THEN 500
            ELSE 0
        END AS revenue_points
    FROM customer_data
),

final_classification AS (
    SELECT
        customer_id,
        customer_segment,
        leadtime_days,
        total_stay_nights,
        previous_cancellations,
        reserved_room_type,
        average_daily_rate,
        estimated_revenue,                                             -- ① passed through to final SELECT
        (stay_loyalty_points + repeat_customer_points + cancellation_penalty_points + room_type_points + spending_points + reservation_status_points + revenue_points) AS total_loyalty_score
    FROM customer_classification
)

SELECT
    customer_id,
    customer_segment,
    leadtime_days,
    total_stay_nights,
    previous_cancellations,
    reserved_room_type,
    average_daily_rate,
    estimated_revenue,                                              -- ① passed through to final SELECT
    total_loyalty_score,
    CASE
        WHEN total_loyalty_score >= 3000 AND customer_segment = 'Loyal' THEN 'Elite'
        WHEN total_loyalty_score >= 2700 AND customer_segment = 'Loyal' THEN 'Diamond' -- ② fixed threshold
        WHEN total_loyalty_score >= 2500 AND customer_segment = 'Loyal' THEN 'Platinum' -- ② fixed threshold
        WHEN total_loyalty_score >= 2500 THEN 'Gold'
        WHEN total_loyalty_score >= 2000 THEN 'Silver'
        WHEN total_loyalty_score >= 1000 THEN 'Bronze'
        WHEN total_loyalty_score >= 500  THEN 'Copper'
        WHEN total_loyalty_score >= 250  THEN 'Iron'
        ELSE 'Standard'
    END AS loyalty_tier
FROM final_classification
