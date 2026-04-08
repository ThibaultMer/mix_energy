{{ config(
    alias='nat_tr_predi',
    materialized='table'
) }}

SELECT
consommation,
prevision_j1,
prevision_j,
EXTRACT(YEAR FROM date_heure) AS year,
EXTRACT(MONTH FROM date_heure) AS month,
EXTRACT(DAY FROM date_heure) AS day,
EXTRACT(HOUR FROM date_heure) AS hour,
EXTRACT(MINUTE FROM date_heure) AS minute
FROM {{ source('nat_source', 'eco2mix_national_tr') }}
WHERE EXTRACT(YEAR FROM date_heure) = EXTRACT(YEAR FROM CURRENT_DATE())
and consommation is not null
order by date_heure asc
