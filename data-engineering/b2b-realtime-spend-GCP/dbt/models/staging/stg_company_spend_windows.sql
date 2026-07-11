with source as (

    select * from {{ source('raw', 'company_spend_windows') }}

),

cleaned as (

    select
        company_id,
        company_name,
        company_size_tier,

        parse_timestamp('%Y-%m-%dT%H:%M:%E*S%Ez', window_start) as window_start,
        parse_timestamp('%Y-%m-%dT%H:%M:%E*S%Ez', window_end)   as window_end,

        cast(transaction_count as integer)      as transaction_count,
        cast(total_amount_usd as numeric)       as total_amount_usd,
        cast(max_amount_usd as numeric)         as max_amount_usd,
        cast(avg_amount_usd as numeric)         as avg_amount_usd,
        cast(risk_flagged_count as integer)     as risk_flagged_count,
        coalesce(any_risk_flag, false)          as any_risk_flag

    from source
    where company_id is not null
      and window_start is not null

)

select * from cleaned