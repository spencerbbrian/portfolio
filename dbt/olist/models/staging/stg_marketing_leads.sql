WITH marketing_leads AS (
    SELECT 
        mql_id AS marketing_qualified_lead_id,
        DATE(first_contact_date) AS first_contact_date,
        landing_page_id,
        origin AS lead_origin
    FROM {{ source('olist', 'marketing_qualified_leads') }}
    WHERE mql_id IS NOT NULL AND first_contact_date IS NOT NULL
)

SELECT *
FROM marketing_leads