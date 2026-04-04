{{ config(
    alias='nat_tr_agre_j',
    materialized='incremental',
    unique_key='date'
) }}

SELECT
    perimetre,
    nature,
    DATE(date) AS date,
    EXTRACT(YEAR FROM date) AS annee,
    EXTRACT(MONTH FROM date) AS mois,
    EXTRACT(DAY FROM date) AS jour,
    SUM(SAFE_CAST(consommation AS FLOAT64) - SAFE_CAST(pompage AS FLOAT64) - SAFE_CAST(ech_physiques AS FLOAT64)) * 0.25 AS production,
    SUM(SAFE_CAST(consommation AS FLOAT64)) * 0.25 AS consommation,
    SUM(SAFE_CAST(prevision_j1 AS FLOAT64)) * 0.25 AS prevision_j1,
    SUM(SAFE_CAST(prevision_j AS FLOAT64)) * 0.25 AS prevision_j,
    SUM(SAFE_CAST(fioul AS FLOAT64)) * 0.25 AS fioul,
    SUM(SAFE_CAST(charbon AS FLOAT64)) * 0.25 AS charbon,
    SUM(SAFE_CAST(gaz AS FLOAT64)) * 0.25 AS gaz,
    SUM(SAFE_CAST(nucleaire AS FLOAT64)) * 0.25 AS nucleaire,
    SUM(SAFE_CAST(eolien AS FLOAT64)) * 0.25 AS eolien,
    SUM(SAFE_CAST(eolien_terrestre AS FLOAT64)) * 0.25 AS eolien_terrestre,
    SUM(SAFE_CAST(eolien_offshore AS FLOAT64)) * 0.25 AS eolien_offshore,
    SUM(SAFE_CAST(solaire AS FLOAT64)) * 0.25 AS solaire,
    SUM(SAFE_CAST(hydraulique AS FLOAT64)) * 0.25 AS hydraulique,
    SUM(SAFE_CAST(pompage AS FLOAT64)) * 0.25 AS pompage,
    SUM(SAFE_CAST(bioenergies AS FLOAT64)) * 0.25 AS bioenergies,
    SUM(SAFE_CAST(ech_physiques AS FLOAT64)) * 0.25 AS ech_physiques,
    SUM(SAFE_CAST(taux_co2 AS FLOAT64) * (SAFE_CAST(consommation AS FLOAT64) - SAFE_CAST(pompage AS FLOAT64) - SAFE_CAST(ech_physiques AS FLOAT64))) / NULLIF(SUM(SAFE_CAST(consommation AS FLOAT64) - SAFE_CAST(pompage AS FLOAT64) - SAFE_CAST(ech_physiques AS FLOAT64)), 0) AS taux_co2,
    SUM(SAFE_CAST(ech_comm_angleterre AS FLOAT64)) * 0.25 AS ech_comm_angleterre,
    SUM(SAFE_CAST(ech_comm_espagne AS FLOAT64)) * 0.25 AS ech_comm_espagne,
    SUM(SAFE_CAST(ech_comm_italie AS FLOAT64)) * 0.25 AS ech_comm_italie,
    SUM(SAFE_CAST(ech_comm_suisse AS FLOAT64)) * 0.25 AS ech_comm_suisse,
    SUM(SAFE_CAST(ech_comm_allemagne_belgique AS FLOAT64)) * 0.25 AS ech_comm_allemagne_belgique,
    SUM(SAFE_CAST(fioul_tac AS FLOAT64)) * 0.25 AS fioul_tac,
    SUM(SAFE_CAST(fioul_cogen AS FLOAT64)) * 0.25 AS fioul_cogen,
    SUM(SAFE_CAST(fioul_autres AS FLOAT64)) * 0.25 AS fioul_autres,
    SUM(SAFE_CAST(gaz_tac AS FLOAT64)) * 0.25 AS gaz_tac,
    SUM(SAFE_CAST(gaz_cogen AS FLOAT64)) * 0.25 AS gaz_cogen,
    SUM(SAFE_CAST(gaz_ccg AS FLOAT64)) * 0.25 AS gaz_ccg,
    SUM(SAFE_CAST(gaz_autres AS FLOAT64)) * 0.25 AS gaz_autres,
    SUM(SAFE_CAST(hydraulique_fil_eau_eclusee AS FLOAT64)) * 0.25 AS hydraulique_fil_eau_eclusee,
    SUM(SAFE_CAST(hydraulique_lacs AS FLOAT64)) * 0.25 AS hydraulique_lacs,
    SUM(SAFE_CAST(hydraulique_step_turbinage AS FLOAT64)) * 0.25 AS hydraulique_step_turbinage,
    SUM(SAFE_CAST(bioenergies_dechets AS FLOAT64)) * 0.25 AS bioenergies_dechets,
    SUM(SAFE_CAST(bioenergies_biomasse AS FLOAT64)) * 0.25 AS bioenergies_biomasse,
    SUM(SAFE_CAST(bioenergies_biogaz AS FLOAT64)) * 0.25 AS bioenergies_biogaz,
    SUM(SAFE_CAST(stockage_batterie AS FLOAT64)) * 0.25 AS stockage_batterie,
    SUM(SAFE_CAST(destockage_batterie AS FLOAT64)) * 0.25 AS destockage_batterie
FROM {{ source('nat_source', 'eco2mix_national_tr') }}
    {% if is_incremental() %}
        WHERE date >= (SELECT DATE_SUB(MAX(date), INTERVAL 2 DAY) FROM {{ this }})
    {% endif %}
GROUP BY perimetre, nature, date, annee, mois, jour
ORDER BY date ASC
