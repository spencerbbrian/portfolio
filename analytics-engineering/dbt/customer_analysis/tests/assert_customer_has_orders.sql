SELECT c.customer_id
FROM {{ ref('stg_customers') }} c
LEFT JOIN {{ ref('stg_orders') }} o
    ON c.customer_id  = o.customer_id
WHERE o.order_id IS NULL