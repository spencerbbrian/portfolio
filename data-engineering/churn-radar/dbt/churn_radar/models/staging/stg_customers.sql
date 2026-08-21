with customers as (

    select
        customer_id,
        company_name,
        industry,
        plan_tier,
        employee_count_band,
        country,
        cast(signup_date as timestamp) as signup_at,
        mrr,
        status,
        cast(updated_at as timestamp) as updated_at
    from {{ source('churn_radar', 'customers') }}

)

select * from customers
