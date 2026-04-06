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
sum((consommation - pompage  - ech_physiques)) *0.5 as production,
sum(consommation) * 0.5 as consommation,
sum(prevision_j1) * 0.25 as prevision_j1,
sum(prevision_j) * 0.25 as prevision_j,
sum(fioul) * 0.5 as fioul,
sum(charbon) * 0.5 as charbon,
sum(gaz) * 0.5 as gaz,
sum(nucleaire) * 0.5 as nucleaire,
sum(eolien) * 0.5 as eolien,
sum(solaire) * 0.5 as solaire,
sum(hydraulique) * 0.5 as hydraulique,
sum(pompage) * 0.5 as pompage,
sum(bioenergies) * 0.5 as bioenergies,
sum(ech_physiques) * 0.5 as ech_physiques,
sum(taux_co2  * (consommation - pompage  - ech_physiques)) / NULLIF(sum((consommation - pompage  - ech_physiques)), 0) AS taux_co2
from {{ ref('eco2mix_national_cons_def_histo') }}
{% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }})
{% endif %}
group by perimetre, nature, date, annee, mois, jour
order by date asc
