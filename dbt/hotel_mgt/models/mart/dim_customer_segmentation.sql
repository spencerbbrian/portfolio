{{ config(materialized='table') }}

WITH source AS (
    SELECT
        customer_id,
        customer_segment,
        loyalty_tier,
        leadtime_days,
        total_stay_nights,
        previous_cancellations,
        average_daily_rate,
        total_loyalty_score
    FROM {{ ref('int_customer_segments') }}
),

grouped AS (
    SELECT
        customer_segment,
        loyalty_tier,

        -- Volume
        COUNT(customer_id)                                              AS customer_count,

        -- Lead time & stay behavior
        ROUND(AVG(leadtime_days), 1)                                    AS avg_leadtime_days,
        ROUND(AVG(total_stay_nights), 1)                                AS avg_stay_nights,
        SUM(total_stay_nights)                                          AS total_stay_nights,

        -- Cancellation rate
        ROUND(
            SUM(CASE WHEN previous_cancellations > 0 THEN 1 ELSE 0 END)
            * 100.0 / NULLIF(COUNT(customer_id), 0),
            2
        )                                                               AS cancellation_rate_pct,

        -- Spend
        ROUND(AVG(average_daily_rate), 2)                               AS avg_daily_rate,
        ROUND(SUM(average_daily_rate), 2)                               AS total_revenue_proxy,

        -- Loyalty score distribution
        ROUND(AVG(total_loyalty_score), 1)                              AS avg_loyalty_score,
        MIN(total_loyalty_score)                                        AS min_loyalty_score,
        MAX(total_loyalty_score)                                        AS max_loyalty_score

    FROM source
    GROUP BY
        customer_segment,
        loyalty_tier
)

SELECT
    customer_segment,
    loyalty_tier,
    customer_count,
    avg_leadtime_days,
    avg_stay_nights,
    total_stay_nights,
    cancellation_rate_pct,
    avg_daily_rate,
    total_revenue_proxy,
    avg_loyalty_score,
    min_loyalty_score,
    max_loyalty_score,

    -- Share within tier (e.g. what % of Gold customers are Loyal vs Occasional)
    ROUND(
        customer_count * 100.0 / NULLIF(SUM(customer_count) OVER (PARTITION BY loyalty_tier), 0),
        2
    )                                                                   AS pct_of_tier,

    -- Share within segment (e.g. what % of Loyal customers are Gold vs Silver)
    ROUND(
        customer_count * 100.0 / NULLIF(SUM(customer_count) OVER (PARTITION BY customer_segment), 0),
        2
    )                                                                   AS pct_of_segment

FROM grouped
ORDER BY
    loyalty_tier,
    customer_segment