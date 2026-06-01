WITH order_items AS (
    SELECT
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_due_date,
        price,
        freight_value
    FROM {{ ref('stg_order_items') }}
)

SELECT
    order_id,
    sum(price) as total_items_price,
    sum(freight_value) as total_freight_value,
    sum(price + freight_value) as total_order_item_value,
    count(distinct product_id) as unique_products_count,
    count(distinct seller_id) as unique_sellers_count,
    count(order_item_id) as total_items_count
FROM order_items
GROUP BY order_id