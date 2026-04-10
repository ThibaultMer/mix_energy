{{ config(
    alias='reg_tr_predi',
    materialized='table'
) }}

SELECT
code_insee_region,
date_heure,
consommation,
-- Moyenne depuis le début jusqu'à t-1
IFNULL(AVG(consommation) OVER (
  PARTITION BY code_insee_region
  ORDER BY date_heure asc
  ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
),0) AS prev_conso_mean,
-- Moyenne sur les 4 valeurs précédentes (1 heure)
IFNULL(AVG(consommation) OVER (
  PARTITION BY code_insee_region
  ORDER BY date_heure asc
  ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
),0) AS prev_conso_mean_h,
-- Moyenne sur les 30 derniers jours (fenêtre temporelle)
IFNULL(AVG(consommation) OVER (
  PARTITION BY code_insee_region
  ORDER BY date_heure asc
  ROWS BETWEEN 2880 PRECEDING AND 1 PRECEDING
),0) AS prev_conso_mean_m,
EXTRACT(YEAR FROM date_heure) AS year,
EXTRACT(MONTH FROM date_heure) AS month,
EXTRACT(DAY FROM date_heure) AS day,
EXTRACT(HOUR FROM date_heure) AS hour,
EXTRACT(MINUTE FROM date_heure) AS minute
FROM {{ source('reg_source', 'eco2mix_regional_tr') }}
WHERE EXTRACT(YEAR FROM date_heure) = EXTRACT(YEAR FROM CURRENT_DATE()) and date_heure < (select min(date_heure) from {{ source('reg_source', 'eco2mix_regional_tr') }} where consommation is null)
order by code_insee_region, date_heure asc
