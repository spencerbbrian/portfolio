{{
    config(
        materialized='incremental',
        unique_keys='order_id',
    )
}}


SELECT 
    order_id,
    customer_id,
    order_date::date AS order_date,
    amount::numeric(10,2) AS order_amount,
    order_status
FROM {{ source('raw', 'orders') }}

{% if is_incremental() %}
    WHERE order_date > (SELECT MAX(order_date) FROM {{ this }})
{% endif %}