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
    (SUM(consommation) - SUM(pompage) - SUM(ech_physiques)) * 0.25 AS production,
    SUM(consommation) * 0.25 AS consommation,
    SUM(thermique) * 0.25 AS thermique,
    SUM(nucleaire) * 0.25 AS nucleaire,
    SUM(eolien) * 0.25 AS eolien,
    SUM(solaire) * 0.25 AS solaire,
    SUM(hydraulique) * 0.25 AS hydraulique,
    SUM(pompage) * 0.25 AS pompage,
    SUM(bioenergies) * 0.25 AS bioenergies,
    SUM(ech_physiques) * 0.25 AS ech_physiques,
    SUM(tco_thermique * thermique) / NULLIF(SUM(thermique), 0) AS tco_thermique,
    SUM(tch_thermique * consommation) / NULLIF(SUM(consommation), 0) AS tch_thermique,
    SUM(tco_nucleaire * nucleaire) / NULLIF(SUM(nucleaire), 0) AS tco_nucleaire,
    SUM(tch_nucleaire * consommation) / NULLIF(SUM(consommation), 0) AS tch_nucleaire,
    SUM(tco_eolien * eolien) / NULLIF(SUM(eolien), 0) AS tco_eolien,
    SUM(tch_eolien * consommation) / NULLIF(SUM(consommation), 0) AS tch_eolien,
    SUM(tco_solaire * solaire) / NULLIF(SUM(solaire), 0) AS tco_solaire,
    SUM(tch_solaire * consommation) / NULLIF(SUM(consommation), 0) AS tch_solaire,
    SUM(tco_hydraulique * hydraulique) / NULLIF(SUM(hydraulique), 0) AS tco_hydraulique,
    SUM(tch_hydraulique * consommation) / NULLIF(SUM(consommation), 0) AS tch_hydraulique,
    SUM(tco_bioenergies * bioenergies) / NULLIF(SUM(bioenergies), 0) AS tco_bioenergies,
    SUM(tch_bioenergies * consommation) / NULLIF(SUM(consommation), 0) AS tch_bioenergies
FROM {{ source('reg_source', 'eco2mix_regional_tr') }}
    {% if is_incremental() %}
        WHERE date >= (SELECT DATE_SUB(MAX(date), INTERVAL 2 DAY) FROM {{ this }})
    {% endif %}
GROUP BY code_insee_region, libelle_region, nature, date, annee, mois, jour
ORDER BY date, libelle_region ASC
