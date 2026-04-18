{{ config(
    alias='eco2mix_regional_cons_def_histo',
    materialized='incremental',
    unique_key='date'
) }}

SELECT
code_insee_region AS code_insee_region,
libelle_region    AS libelle_region,
nature            AS nature,
date              AS date,
heure             AS heure,
date_heure        AS date_heure,
consommation      AS consommation,
thermique         AS thermique,
nucleaire         AS nucleaire,
eolien            AS eolien,
solaire           AS solaire,
hydraulique       AS hydraulique,
pompage           AS pompage,
bioenergies       AS bioenergies,
ech_physiques     AS ech_physiques,
SAFE_CAST(tco_thermique AS FLOAT64)      AS tco_thermique,
SAFE_CAST(tch_thermique AS FLOAT64)      AS tch_thermique,
SAFE_CAST(tco_nucleaire AS FLOAT64)      AS tco_nucleaire,
SAFE_CAST(tch_nucleaire AS FLOAT64)      AS tch_nucleaire,
SAFE_CAST(tco_eolien AS FLOAT64)         AS tco_eolien,
SAFE_CAST(tch_eolien AS FLOAT64)         AS tch_eolien,
SAFE_CAST(tco_solaire AS FLOAT64)        AS tco_solaire,
SAFE_CAST(tch_solaire AS FLOAT64)        AS tch_solaire,
SAFE_CAST(tco_hydraulique AS FLOAT64)    AS tco_hydraulique,
SAFE_CAST(tch_hydraulique AS FLOAT64)    AS tch_hydraulique,
SAFE_CAST(tco_bioenergies AS FLOAT64)    AS tco_bioenergies,
SAFE_CAST(tch_bioenergies AS FLOAT64)    AS tch_bioenergies
FROM {{source('reg_source','eco2mix_regional_cons_def')}}

{% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }}) AND consommation is not NULL
{% endif %}
