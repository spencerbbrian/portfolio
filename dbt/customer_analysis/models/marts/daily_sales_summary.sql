{{
    config(
        materialized='view',
        unique_keys='order_date',
    )
}}

SELECT
    order_date,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(CASE WHEN order_status = 'completed' THEN 1 ELSE 0 END ) AS total_completed_orders,
    SUM(CASE WHEN order_status = 'pending' THEN 1 ELSE 0 END ) AS total_pending_orders,
    SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END ) AS total_cancelled_orders,
    SUM(CASE WHEN order_status = 'returned' THEN 1 ELSE 0 END ) AS total_returned_orders,
    SUM(CASE WHEN order_status = 'shipped' THEN 1 ELSE 0 END ) AS total_shipped_orders,
    SUM(CASE WHEN order_status = 'completed' THEN  order_amount ELSE 0 END)  AS total_completed_sales,
    SUM(CASE WHEN order_status = 'returned' THEN  order_amount ELSE 0 END)  AS total_returned_sales,
    (total_completed_sales - total_returned_sales) AS total_net_sales
FROM {{ ref('stg_orders') }}
GROUP BY order_date
ORDER BY order_date DESC