{{ config(materialized='table') }}

WITH source AS (
    SELECT * FROM {{ ref('int_cancellations_deep_dive') }}
),

-- ----------------------------------------------------------------
-- KPI 1: Cancellation volume & revenue lost
-- ----------------------------------------------------------------
cancellation_revenue AS (
    SELECT
        hotel,
        deposit_type,
        market_segment,
        distribution_channel,
        customer_type,
        reserved_room_type,

        COUNT(*)                                                        AS total_bookings,
        SUM(CASE WHEN is_canceled = 'TRUE' THEN 1 ELSE 0 END)          AS total_cancellations,
        ROUND(
            SUM(CASE WHEN is_canceled = 'TRUE' THEN 1 ELSE 0 END)
            * 100.0 / NULLIF(COUNT(*), 0), 2
        )                                                               AS cancellation_rate_pct,

        ROUND(SUM(revenue_lost), 2)                                     AS total_revenue_lost,
        ROUND(AVG(
            CASE WHEN is_canceled = 'TRUE' THEN average_daily_rate END
        ), 2)                                                           AS avg_adr_canceled,
        ROUND(AVG(
            CASE WHEN is_canceled = 'FALSE' THEN average_daily_rate END
        ), 2)                                                           AS avg_adr_retained,

        -- Late cancellation breakdown
        SUM(CASE WHEN is_late_cancellation THEN 1 ELSE 0 END)          AS late_cancellation_count,
        ROUND(SUM(
            CASE WHEN is_late_cancellation THEN revenue_lost ELSE 0 END
        ), 2)                                                           AS late_cancellation_revenue_lost

    FROM source
    GROUP BY
        hotel,
        deposit_type,
        market_segment,
        distribution_channel,
        customer_type,
        reserved_room_type
),

-- ----------------------------------------------------------------
-- KPI 2: Lead time profile — canceled vs non-canceled
-- ----------------------------------------------------------------
lead_time_profile AS (
    SELECT
        hotel,
        deposit_type,
        market_segment,
        distribution_channel,
        customer_type,
        reserved_room_type,
        is_canceled,

        ROUND(AVG(leadtime_days), 1)                                    AS avg_leadtime_days,
        MIN(leadtime_days)                                              AS min_leadtime_days,
        MAX(leadtime_days)                                              AS max_leadtime_days,

        COUNTIF(leadtime_days < 7)                                      AS booked_last_week,
        COUNTIF(leadtime_days BETWEEN 7  AND 30)                        AS booked_1_to_4_weeks,
        COUNTIF(leadtime_days BETWEEN 31 AND 90)                        AS booked_1_to_3_months,
        COUNTIF(leadtime_days BETWEEN 91 AND 180)                       AS booked_3_to_6_months,
        COUNTIF(leadtime_days > 180)                                    AS booked_6_months_plus

    FROM source
    GROUP BY
        hotel,
        deposit_type,
        market_segment,
        distribution_channel,
        customer_type,
        reserved_room_type,
        is_canceled
),


deposit_effectiveness AS (
    SELECT
        hotel,
        deposit_type,
        market_segment,
        distribution_channel,
        customer_type,
        reserved_room_type,
        deposit_cancellation_outcome,

        COUNT(*)                                                        AS booking_count,
        ROUND(SUM(revenue_lost), 2)                                     AS revenue_lost,
        ROUND(
            SUM(CASE WHEN is_canceled = 'TRUE' THEN 1 ELSE 0 END)
            * 100.0 / NULLIF(COUNT(*), 0), 2
        )                                                               AS cancellation_rate_pct

    FROM source
    GROUP BY
        hotel,
        deposit_type,
        market_segment,
        distribution_channel,
        customer_type,
        reserved_room_type,
        deposit_cancellation_outcome
)

SELECT
    r.hotel,
    r.deposit_type,
    r.market_segment,
    r.distribution_channel,
    r.customer_type,
    r.reserved_room_type,

    -- Cancellation & revenue KPIs
    r.total_bookings,
    r.total_cancellations,
    r.cancellation_rate_pct,
    r.total_revenue_lost,
    r.avg_adr_canceled,
    r.avg_adr_retained,
    r.late_cancellation_count,
    r.late_cancellation_revenue_lost,

    -- Lead time KPIs (canceled bookings only)
    l.avg_leadtime_days                                                 AS avg_leadtime_canceled,
    l.min_leadtime_days                                                 AS min_leadtime_canceled,
    l.max_leadtime_days                                                 AS max_leadtime_canceled,
    l.booked_last_week,
    l.booked_1_to_4_weeks,
    l.booked_1_to_3_months,
    l.booked_3_to_6_months,
    l.booked_6_months_plus,

    -- Deposit effectiveness
    d.deposit_cancellation_outcome,
    d.cancellation_rate_pct                                             AS deposit_type_cancellation_rate_pct

FROM cancellation_revenue r
LEFT JOIN lead_time_profile l
    ON  r.hotel                 = l.hotel
    AND r.deposit_type          = l.deposit_type
    AND r.market_segment        = l.market_segment
    AND r.distribution_channel  = l.distribution_channel
    AND r.customer_type         = l.customer_type
    AND r.reserved_room_type    = l.reserved_room_type
    AND l.is_canceled           = 'TRUE'
LEFT JOIN deposit_effectiveness d
    ON  r.hotel                 = d.hotel
    AND r.deposit_type          = d.deposit_type
    AND r.market_segment        = d.market_segment
    AND r.distribution_channel  = d.distribution_channel
    AND r.customer_type         = d.customer_type
    AND r.reserved_room_type    = d.reserved_room_type

ORDER BY
    r.total_revenue_lost DESC