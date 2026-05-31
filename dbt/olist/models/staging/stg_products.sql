WITH products_data AS (
    SELECT 
        products.product_id,
        category_translation.product_category_name_english AS category_name,
        products.product_name_lenght AS name_lenght,
        products.product_description_lenght AS description_lenght,
        products.product_photos_qty AS photos_qty,
        products.product_weight_g AS weight_g,
        products.product_length_cm AS length_cm,
        products.product_height_cm AS height_cm,
        products.product_width_cm AS width_cm
    FROM {{ source('olist', 'products') }} AS products
    LEFT JOIN {{ source('olist', 'product_category_name_translation') }} AS category_translation
        ON products.product_category_name = category_translation.product_category_name
    WHERE products.product_id IS NOT NULL
)

SELECT *
FROM products_data