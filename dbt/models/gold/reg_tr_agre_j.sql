{{ config (
    alias='reg_tr_agre_j',
    materialized='incremental',
    unique_key=['date', 'code_insee_region']
) }}

SELECT
    code_insee_region,
    libelle_region,
    nature,
    DATE(date) AS date,
    EXTRACT(YEAR FROM date) AS annee,
    EXTRACT(MONTH FROM date) AS mois,
    EXTRACT(DAY FROM date) AS jour,
    (SUM(SAFE_CAST(consommation AS FLOAT64)) - SUM(SAFE_CAST(pompage AS FLOAT64)) - SUM(SAFE_CAST(ech_physiques AS FLOAT64))) * 0.25 AS production,
    SUM(SAFE_CAST(consommation AS FLOAT64)) * 0.25 AS consommation,
    SUM(SAFE_CAST(thermique AS FLOAT64)) * 0.25 AS thermique,
    SUM(SAFE_CAST(nucleaire AS FLOAT64)) * 0.25 AS nucleaire,
    SUM(SAFE_CAST(eolien AS FLOAT64)) * 0.25 AS eolien,
    SUM(SAFE_CAST(solaire AS FLOAT64)) * 0.25 AS solaire,
    SUM(SAFE_CAST(hydraulique AS FLOAT64)) * 0.25 AS hydraulique,
    SUM(SAFE_CAST(pompage AS FLOAT64)) * 0.25 AS pompage,
    SUM(SAFE_CAST(bioenergies AS FLOAT64)) * 0.25 AS bioenergies,
    SUM(SAFE_CAST(ech_physiques AS FLOAT64)) * 0.25 AS ech_physiques,
    SUM(SAFE_CAST(stockage_batterie AS FLOAT64)) * 0.25 AS stockage_batterie,
    SUM(SAFE_CAST(destockage_batterie AS FLOAT64)) * 0.25 AS destockage_batterie,
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
FROM {{ source('reg_source', 'eco2mix_regional_tr') }}
    {% if is_incremental() %}
        WHERE date >= (SELECT DATE_SUB(MAX(date), INTERVAL 2 DAY) FROM {{ this }})
    {% endif %}
GROUP BY code_insee_region, libelle_region, nature, date, annee, mois, jour
ORDER BY date, libelle_region ASC
