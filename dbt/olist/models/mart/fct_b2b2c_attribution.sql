WITH orders AS (
    SELECT
        order_id,
        customer_id,
        order_status,
        purchase_date,
        total_items_price,
        total_freight_value,
        total_order_item_value,
        total_items_count
    FROM {{ ref('fct_orders') }}
),

order_seller_mapping AS (
    SELECT
        order_id,
        seller_id
    FROM {{ ref('stg_order_items') }}
    GROUP BY 1, 2
),

sellers AS (
    SELECT
        seller_id,
        marketing_channel,
        sales_developer_id,
        sales_representative_id,
        is_funnel_acquired,
        city as seller_city,
        state as seller_state
    FROM {{ ref('dim_sellers') }}
)

SELECT
    o.order_id,
    o.customer_id,
    m.seller_id,
    o.order_status,
    o.purchase_date,
    s.marketing_channel,
    s.sales_developer_id,
    s.sales_representative_id,
    s.is_funnel_acquired,
    s.seller_city,
    s.seller_state,
    o.total_items_price as attributed_revenue,
    o.total_freight_value as attributed_freight,
    o.total_order_item_value as attributed_total_value,
    o.total_items_count
FROM orders as o
INNER JOIN order_seller_mapping as m
    ON o.order_id = m.order_id
LEFT JOIN sellers as s
    ON m.seller_id = s.seller_id