{{ config(
    alias='eco2mix_regional_cons_def_histo',
    materialized='incremental',
    unique_key='date'
) }}

SELECT * FROM {{source('reg_source','eco2mix_regional_cons_def')}}

{% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }})
{% endif %}
