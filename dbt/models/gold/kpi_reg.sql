{{ config(
    alias='kpi_reg',
    materialized='table')
    }}


select
code_insee_region as code_insee_region,
libelle_region as libelle_region,
annee as annee
mois as mois
SUM(production) AS production_totale,
SUM(nucleaire) / SUM(production) AS pct_nucleaire,
SUM(fioul + charbon + gaz) / SUM(production) AS pct_thermique,
SUM(eolien + solaire + hydraulique + bioenergies) / SUM(production) AS pct_renouvelable,
group by code_insee_region, libelle_region, annee, mois
order by code_insee_region asc, annee asc, mois asc
from {{ref('reg_cons_agre_j')}}
