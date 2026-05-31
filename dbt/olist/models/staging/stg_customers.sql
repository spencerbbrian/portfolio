WITH customers AS (
    SELECT 
        customer_id,
        customer_unique_id,
        customer_state,
        customer_zip_code_prefix,
        customer_city
    FROM {{ source('olist', 'customers') }}
    WHERE customer_id IS NOT NULL AND customer_unique_id IS NOT NULL
)

SELECT *
FROM customers