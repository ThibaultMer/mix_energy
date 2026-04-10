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
    SUM(consommation - pompage - ech_physiques) * 0.25 AS production,
    SUM(consommation) * 0.25 AS consommation,
    SUM(prevision_j1) * 0.25 AS prevision_j1,
    SUM(prevision_j) * 0.25 AS prevision_j,
    SUM(fioul) * 0.25 AS fioul,
    SUM(charbon) * 0.25 AS charbon,
    SUM(gaz) * 0.25 AS gaz,
    SUM(nucleaire) * 0.25 AS nucleaire,
    SUM(eolien) * 0.25 AS eolien,
    SUM(solaire) * 0.25 AS solaire,
    SUM(hydraulique) * 0.25 AS hydraulique,
    SUM(pompage) * 0.25 AS pompage,
    SUM(bioenergies) * 0.25 AS bioenergies,
    SUM(ech_physiques) * 0.25 AS ech_physiques,
    SUM(taux_co2 * (consommation - pompage - ech_physiques)) / NULLIF(SUM(consommation - pompage - ech_physiques), 0) AS taux_co2

FROM {{ source('nat_source', 'eco2mix_national_tr') }}
    {% if is_incremental() %}
        WHERE date >= (SELECT DATE_SUB(MAX(date), INTERVAL 2 DAY) FROM {{ this }})
    {% endif %}
GROUP BY perimetre, nature, date, annee, mois, jour
ORDER BY date ASC
