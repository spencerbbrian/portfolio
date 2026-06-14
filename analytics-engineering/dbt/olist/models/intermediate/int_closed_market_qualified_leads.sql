WITH marketing_leads AS (
    SELECT
        marketing_qualified_lead_id,
        first_contact_date,
        landing_page_id,
        marketing_channel
    FROM {{ ref('stg_marketing_leads') }}
),

closed_deals AS (
    SELECT
        marketing_qualified_lead_id,
        seller_id,
        sales_developer_id,
        sales_representative_id,
        deal_close_date,
        business_segment,
        lead_type,
        lead_behaviour_profile,
        associated_to_a_company,
        has_global_trade_item_number,
        average_stock,
        business_type,
        declared_product_catalog_size,
        declared_monthly_revenue
    FROM {{ ref('stg_closed_deals') }}
)

SELECT
    mql.marketing_qualified_lead_id,
    deals.seller_id,
    deals.sales_developer_id,
    deals.sales_representative_id,
    mql.first_contact_date,
    mql.landing_page_id,
    coalesce(mql.marketing_channel, 'unknown') as marketing_channel,
    deals.deal_close_date,
    deals.business_segment,
    deals.lead_type,
    deals.lead_behaviour_profile,
    deals.business_type,
    CASE 
        WHEN deals.seller_id IS NOT NULL THEN true 
        ELSE false 
    END as is_won_deal
FROM marketing_leads as mql
LEFT JOIN closed_deals as deals 
    ON mql.marketing_qualified_lead_id = deals.marketing_qualified_lead_id