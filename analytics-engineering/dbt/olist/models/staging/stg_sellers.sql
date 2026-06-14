WITH sellers_data AS (
    SELECT 
        seller_id,
        seller_zip_code_prefix AS zip_code_prefix,
        seller_city AS city,
        seller_state AS state
    FROM {{ source('olist', 'sellers') }}
    WHERE seller_id IS NOT NULL
)

SELECT *
FROM sellers_data