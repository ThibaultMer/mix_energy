-- Calcul de production journalière nationale
{{ config(
    alias='nat_cons_agre_j',
    materialized='incremental',
    unique_key='date') }}

select
perimetre as perimetre,
nature as nature,
DATE(date) as date,
EXTRACT(YEAR FROM date) AS annee,
EXTRACT(MONTH FROM date) AS mois,
EXTRACT(DAY FROM date) AS jour,
sum((SAFE_CAST(consommation AS FLOAT64)- SAFE_CAST(pompage AS FLOAT64) - SAFE_CAST(ech_physiques AS FLOAT64))) *0.5 as production,
sum(SAFE_CAST(consommation AS FLOAT64)) * 0.5 as consommation,
sum(SAFE_CAST(prevision_j1 AS FLOAT64)) * 0.25 as prevision_j1,
sum(SAFE_CAST(prevision_j AS FLOAT64)) * 0.25 as prevision_j,
sum(SAFE_CAST(fioul AS FLOAT64)) * 0.5 as fioul,
sum(SAFE_CAST(charbon AS FLOAT64)) * 0.5 as charbon,
sum(SAFE_CAST(gaz AS FLOAT64)) * 0.5 as gaz,
sum(SAFE_CAST(nucleaire AS FLOAT64)) * 0.5 as nucleaire,
sum(SAFE_CAST(eolien AS FLOAT64)) * 0.5 as eolien,
sum(SAFE_CAST(solaire AS FLOAT64)) * 0.5 as solaire,
sum(SAFE_CAST(hydraulique AS FLOAT64)) * 0.5 as hydraulique,
sum(SAFE_CAST(pompage AS FLOAT64)) * 0.5 as pompage,
sum(SAFE_CAST(bioenergies AS FLOAT64)) * 0.5 as bioenergies,
sum(SAFE_CAST(ech_physiques AS FLOAT64)) * 0.5 as ech_physiques,
sum(SAFE_CAST(taux_co2 AS FLOAT64) * (SAFE_CAST(consommation AS FLOAT64)- SAFE_CAST(pompage AS FLOAT64) - SAFE_CAST(ech_physiques AS FLOAT64))) / NULLIF(sum((SAFE_CAST(consommation AS FLOAT64)- SAFE_CAST(pompage AS FLOAT64) - SAFE_CAST(ech_physiques AS FLOAT64))), 0) AS taux_co2,
sum(SAFE_CAST(ech_comm_angleterre AS FLOAT64)) * 0.5 as ech_comm_angleterre,
sum(SAFE_CAST(ech_comm_espagne AS FLOAT64)) * 0.5 as ech_comm_espagne,
sum(SAFE_CAST(ech_comm_italie AS FLOAT64)) * 0.5 as ech_comm_italie,
sum(SAFE_CAST(ech_comm_suisse AS FLOAT64)) * 0.5 as ech_comm_suisse,
sum(SAFE_CAST(ech_comm_allemagne_belgique AS FLOAT64)) * 0.5 as ech_comm_allemagne_belgique,
sum(SAFE_CAST(fioul_tac AS FLOAT64)) * 0.5 as fioul_tac,
sum(SAFE_CAST(fioul_cogen AS FLOAT64)) * 0.5 as fioul_cogen,
sum(SAFE_CAST(fioul_autres AS FLOAT64)) * 0.5 as fioul_autres,
sum(SAFE_CAST(gaz_tac AS FLOAT64)) * 0.5 as gaz_tac,
sum(SAFE_CAST(gaz_cogen AS FLOAT64)) * 0.5 as gaz_cogen,
sum(SAFE_CAST(gaz_ccg AS FLOAT64)) * 0.5 as gaz_ccg,
sum(SAFE_CAST(gaz_autres AS FLOAT64)) * 0.5 as gaz_autres,
sum(SAFE_CAST(hydraulique_fil_eau_eclusee AS FLOAT64)) * 0.5 as hydraulique_fil_eau_eclusee,
sum(SAFE_CAST(hydraulique_lacs AS FLOAT64)) * 0.5 as hydraulique_lacs,
sum(SAFE_CAST(hydraulique_step_turbinage AS FLOAT64)) * 0.5 as hydraulique_step_turbinage,
sum(SAFE_CAST(bioenergies_dechets AS FLOAT64)) * 0.5 as bioenergies_dechets,
sum(SAFE_CAST(bioenergies_biomasse AS FLOAT64)) * 0.5 as bioenergies_biomasse,
sum(SAFE_CAST(bioenergies_biogaz AS FLOAT64)) * 0.5 as bioenergies_biogaz
from {{ ref('eco2mix_national_cons_def_histo') }}
group by perimetre, nature, date, annee, mois, jour
order by date asc

{% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }})
{% endif %}
