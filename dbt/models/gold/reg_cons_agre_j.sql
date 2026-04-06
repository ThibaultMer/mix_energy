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
(sum(consommation)- sum(pompage) - sum(ech_physiques)) *0.25 as production,
sum(consommation) * 0.25 as consommation,
sum(thermique) * 0.25 as thermique,
sum(nucleaire) * 0.25 as nucleaire,
sum(eolien) * 0.25 as eolien,
sum(solaire) * 0.25 as solaire,
sum(hydraulique) * 0.25 as hydraulique,
sum(pompage) * 0.25 as pompage,
sum(bioenergies) * 0.25 as bioenergies,
sum(ech_physiques) * 0.25 as ech_physiques,
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
from {{ ref('eco2mix_regional_cons_def_histo') }}
{% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }})
{% endif %}
group by code_insee_region, libelle_region, nature, date, annee, mois, jour
order by date, libelle_region asc
