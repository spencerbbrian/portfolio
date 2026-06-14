WITH order_reviews_data AS (
    SELECT 
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        DATE(review_creation_date) AS review_creation_date,
        DATE(review_answer_timestamp) AS review_answer_timestamp
    FROM {{ source('olist', 'order_reviews') }}
    WHERE review_id IS NOT NULL AND order_id IS NOT NULL
)

SELECT *
FROM order_reviews_data