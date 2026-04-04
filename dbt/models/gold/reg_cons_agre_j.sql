{{ config(
    alias='reg_cons_agre_j',
    materialized='incremental',
    unique_key='date') }}

select
code_insee_region as code_insee_region,
libelle_region as libelle_region,
nature as nature,
date(date) as date,
EXTRACT(YEAR FROM date) AS annee,
EXTRACT(MONTH FROM date) AS mois,
EXTRACT(DAY FROM date) AS jour,
(sum(SAFE_CAST(consommation AS FLOAT64))- sum(SAFE_CAST(pompage AS FLOAT64)) - sum(SAFE_CAST(ech_physiques AS FLOAT64))) *0.25 as production,
sum(SAFE_CAST(consommation AS FLOAT64)) * 0.25 as consommation,
sum(SAFE_CAST(thermique AS FLOAT64)) * 0.25 as thermique,
sum(SAFE_CAST(nucleaire AS FLOAT64)) * 0.25 as nucleaire,
sum(SAFE_CAST(eolien AS FLOAT64)) * 0.25 as eolien,
sum(SAFE_CAST(solaire AS FLOAT64)) * 0.25 as solaire,
sum(SAFE_CAST(hydraulique AS FLOAT64)) * 0.25 as hydraulique,
sum(SAFE_CAST(pompage AS FLOAT64)) * 0.25 as pompage,
sum(SAFE_CAST(bioenergies AS FLOAT64)) * 0.25 as bioenergies,
sum(SAFE_CAST(ech_physiques AS FLOAT64)) * 0.25 as ech_physiques,
sum(SAFE_CAST(stockage_batterie AS FLOAT64)) * 0.25 as stockage_batterie,
sum(SAFE_CAST(destockage_batterie AS FLOAT64)) * 0.25 as destockage_batterie,
sum(SAFE_CAST(eolien_terrestre AS FLOAT64)) * 0.25 as eolien_terrestre,
sum(SAFE_CAST(eolien_offshore AS FLOAT64)) * 0.25 as eolien_offshore,
SUM(SAFE_CAST(tco_thermique AS FLOAT64) * SAFE_CAST(thermique AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(thermique AS FLOAT64)), 0) AS tco_thermique,
SUM(SAFE_CAST(tch_thermique AS FLOAT64) * SAFE_CAST(consommation AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(consommation AS FLOAT64)), 0) AS tch_thermique,
SUM(SAFE_CAST(tco_nucleaire AS FLOAT64) * SAFE_CAST(nucleaire AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(nucleaire AS FLOAT64)), 0) AS tco_nucleaire,
SUM(SAFE_CAST(tch_nucleaire AS FLOAT64) * SAFE_CAST(consommation AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(consommation AS FLOAT64)), 0) AS tch_nucleaire,
SUM(SAFE_CAST(tco_eolien AS FLOAT64) * SAFE_CAST(eolien AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(eolien AS FLOAT64)), 0) AS tco_eolien,
SUM(SAFE_CAST(tch_eolien AS FLOAT64) * SAFE_CAST(consommation AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(consommation AS FLOAT64)), 0) AS tch_eolien,
SUM(SAFE_CAST(tco_solaire AS FLOAT64) * SAFE_CAST(solaire AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(solaire AS FLOAT64)), 0) AS tco_solaire,
SUM(SAFE_CAST(tch_solaire AS FLOAT64) * SAFE_CAST(consommation AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(consommation AS FLOAT64)), 0) AS tch_solaire,
SUM(SAFE_CAST(tco_hydraulique AS FLOAT64) * SAFE_CAST(hydraulique AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(hydraulique AS FLOAT64)), 0) AS tco_hydraulique,
SUM(SAFE_CAST(tch_hydraulique AS FLOAT64) * SAFE_CAST(consommation AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(consommation AS FLOAT64)), 0) AS tch_hydraulique,
SUM(SAFE_CAST(tco_bioenergies AS FLOAT64) * SAFE_CAST(bioenergies AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(bioenergies AS FLOAT64)), 0) AS tco_bioenergies,
SUM(SAFE_CAST(tch_bioenergies AS FLOAT64) * SAFE_CAST(consommation AS FLOAT64)) / NULLIF(SUM(SAFE_CAST(consommation AS FLOAT64)), 0) AS tch_bioenergies
from {{ ref('eco2mix_regional_cons_def_histo') }}
{% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }})
{% endif %}
group by code_insee_region, libelle_region, nature, date, annee, mois, jour
order by date, libelle_region asc
