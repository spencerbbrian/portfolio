WITH order_payments_data AS (
    SELECT 
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    FROM {{ source('olist', 'order_payments') }}
    WHERE order_id IS NOT NULL
)

SELECT *
FROM order_payments_data