{{ config(
    alias='eco2mix_national_cons_def_histo',
    materialized='incremental',
    unique_key='date'
) }}

SELECT * FROM {{source('nat_source','eco2mix_national_cons_def')}}

{% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }})
{% endif %}
