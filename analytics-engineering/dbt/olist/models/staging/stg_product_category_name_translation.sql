WITH product_category_name_translation_data AS (
    SELECT 
        product_category_name AS category_name,
        product_category_name_english AS category_name_english
    FROM {{ source('olist', 'product_category_name_translation') }}
    WHERE product_category_name IS NOT NULL
)

SELECT *
FROM product_category_name_translation_data