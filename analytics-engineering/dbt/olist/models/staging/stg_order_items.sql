WITH order_items_data AS (
    SELECT 
        order_id,
        order_item_id,
        product_id,
        seller_id,
        DATE(shipping_limit_date) AS shipping_due_date,
        price,
        freight_value
    FROM {{ source('olist', 'order_items') }}
    WHERE order_id IS NOT NULL
)

SELECT *
FROM order_items_data