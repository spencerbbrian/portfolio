WITH sellers AS (
    SELECT
        seller_id,
        zip_code_prefix,
        city,
        state
    FROM {{ ref('stg_sellers') }}
),

closed_market_leads AS (
    SELECT
        seller_id,
        marketing_qualified_lead_id,
        sales_developer_id,
        sales_representative_id,
        first_contact_date,
        landing_page_id,
        marketing_channel,
        deal_close_date,
        business_segment,
        lead_type,
        lead_behaviour_profile,
        business_type,
        is_won_deal
    FROM {{ ref('int_closed_market_qualified_leads') }}
)

SELECT
    s.seller_id,
    cml.marketing_qualified_lead_id,
    cml.sales_developer_id,
    cml.sales_representative_id,
    cml.landing_page_id,
    s.zip_code_prefix,
    s.city,
    s.state,
    coalesce(cml.marketing_channel, 'organic_platform') as marketing_channel,
    cml.first_contact_date,
    cml.deal_close_date,
    cml.business_segment,
    cml.lead_type,
    cml.lead_behaviour_profile,
    cml.business_type,
    CASE 
        WHEN cml.seller_id IS NOT NULL THEN true 
        ELSE false 
    END as is_funnel_acquired

FROM sellers as s
LEFT JOIN closed_market_leads as cml
    ON s.seller_id = cml.seller_id