{{ config(materialized='view') }}

WITH hotel_names_lookup AS (
    SELECT DISTINCT
        hotel_id,
        hotel_name
    FROM {{ ref('stg_bookings') }}
),

daily_revenue AS (
    SELECT
        arrival_date,
        hotel_id,
        ROUND(SUM(estimated_revenue), 2) AS total_revenue
    FROM {{ ref('int_bookings_transformed') }}
    GROUP BY hotel_id, hotel, arrival_date
)

SELECT
    dr.arrival_date,
    dr.hotel_id,
    hnl.hotel_name,
    dr.total_revenue
FROM daily_revenue dr
JOIN hotel_names_lookup hnl
    ON dr.hotel_id = hnl.hotel_id
ORDER BY dr.arrival_date DESC, dr.hotel_id ASC