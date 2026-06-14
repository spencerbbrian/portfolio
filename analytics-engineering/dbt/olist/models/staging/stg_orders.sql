WITH orders AS (
    SELECT 
        order_id,
        customer_id,
        order_status,
        DATE(order_purchase_timestamp) AS purchase_date,
        DATE(order_approved_at) AS approved_date,
        DATE(order_delivered_carrier_date) AS delivered_carrier_date,
        DATE(order_delivered_customer_date) AS delivered_customer_date,
        DATE(order_estimated_delivery_date) AS estimated_delivery_date
    FROM {{ source('olist', 'orders') }}
    WHERE order_id IS NOT NULL AND order_purchase_timestamp IS NOT NULL
)

SELECT *
FROM orders