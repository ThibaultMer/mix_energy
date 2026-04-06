{{ config(
    alias='eco2mix_national_cons_def_histo',
    materialized='incremental',
    unique_key='date'
) }}

SELECT
perimetre       AS perimetre,
nature          AS nature,
date            AS date,
heure           AS heure,
date_heure      AS date_heure,
consommation    AS consommation,
prevision_j1    AS prevision_j1,
prevision_j     AS prevision_j,
fioul           AS fioul,
charbon         AS charbon,
gaz             AS gaz,
nucleaire       AS nucleaire,
eolien          AS eolien,
solaire         AS solaire,
hydraulique     AS hydraulique,
pompage         AS pompage,
bioenergies     AS bioenergies,
ech_physiques   AS ech_physiques,
taux_co2        AS taux_co2
FROM {{source('nat_source','eco2mix_national_cons_def')}}

{% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }})
{% endif %}
