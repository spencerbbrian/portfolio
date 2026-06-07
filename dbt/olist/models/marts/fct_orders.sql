WITH orders AS (
    SELECT
        order_id,
        customer_id,
        order_status,
        purchase_date,
        approved_date,
        delivered_carrier_date,
        delivered_customer_date,
        estimated_delivery_date
    FROM {{ ref('stg_orders') }}
),

order_items_aggregated AS (
    SELECT
        order_id,
        total_items_price,
        total_freight_value,
        total_order_item_value,
        unique_products_count,
        unique_sellers_count,
        total_items_count
    FROM {{ ref('int_order_items_aggregated') }}
)

SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.purchase_date,
    o.approved_date,
    o.delivered_carrier_date,
    o.delivered_customer_date,
    o.estimated_delivery_date,
    coalesce(i.total_items_price, 0.0) as total_items_price,
    coalesce(i.total_freight_value, 0.0) as total_freight_value,
    coalesce(i.total_order_item_value, 0.0) as total_order_item_value,
    coalesce(i.unique_products_count, 0) as unique_products_count,
    coalesce(i.unique_sellers_count, 0) as unique_sellers_count,
    coalesce(i.total_items_count, 0) as total_items_count,
    datediff(day, o.purchase_date, o.delivered_customer_date) as actual_delivery_duration_days,
    datediff(day, o.approved_date, o.estimated_delivery_date) as estimated_delivery_duration_days,
    datediff(day, o.estimated_delivery_date, o.delivered_customer_date) as delivery_delta_vs_estimated_days,
    datediff(day, o.approved_date, o.delivered_carrier_date) as seller_handling_duration_days,
    CASE 
        WHEN o.delivered_customer_date IS NULL THEN 'In Progress / Unfulfilled'
        WHEN o.delivered_customer_date <= o.estimated_delivery_date THEN 'On Time / Early'
        ELSE 'Delayed'
    END AS delivery_performance_status
FROM orders AS o
LEFT JOIN order_items_aggregated AS i
    ON o.order_id = i.order_id