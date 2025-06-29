WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(order_id) AS total_orders,
        SUM(amount) AS total_spend,
    FROM {{ ref('stg_orders') }}
    GROUP BY customer_id
)

SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    co.total_orders,
    {{ currency_format('co.total_spend', '$') }} AS total_spend_formatted
FROM {{ ref('stg_customers') }} c 
LEFT JOIN customer_orders co 
    ON c.customer_id = co.customer_id