{% snapshot snap_sellers %}

{{
    config(
      target_schema='snapshots',
      unique_key='seller_id',
      strategy='check',
      check_cols=['zip_code_prefix', 'city', 'state'],
    )
}}

-- SCD Type 2 history of seller location. Snapshotted straight from the raw
-- source (not stg_sellers) so the change history reflects what actually
-- landed from Olist, before any staging-layer renaming/casting -- standard
-- practice for dbt snapshots.
--
-- Uses `check` strategy rather than `timestamp` because the raw sellers
-- table has no reliable updated_at column to key off of.
select
    seller_id,
    zip_code_prefix,
    city,
    state
from {{ source('olist', 'sellers') }}

{% endsnapshot %}
