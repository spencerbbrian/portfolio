WITH closed_deals AS (
    select
        average_stock,
        business_segment,
        business_type,
        declared_monthly_revenue,
        declared_product_catalog_size,
        has_company AS associated_to_a_company,
        has_gtin AS has_global_trade_item_number,
        lead_behaviour_profile,
        lead_type,
        mql_id AS marketing_qualified_lead_id,
        sdr_id AS sales_developer_id,
        seller_id,
        sr_id AS sales_representative_id,
        DATE(won_date) AS deal_close_date
    from {{ source('olist', 'closed_deals') }}
    where mql_id IS NOT NULL AND won_date IS NOT NULL
)

SELECT *
FROM closed_deals