WITH geolocation AS (
    SELECT 
        geolocation_city AS city,
        geolocation_lat AS latitude,
        geolocation_lng AS longitude,
        geolocation_state AS state,
        geolocation_zip_code_prefix AS zip_code_prefix
    FROM {{ source('olist', 'geolocation') }}
    WHERE geolocation_lat IS NOT NULL AND geolocation_lng IS NOT NULL
)

SELECT *
FROM geolocation