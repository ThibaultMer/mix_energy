{{ config(
    alias='kpi',
    materialized='table')
    }}

select
SUM(production) AS production_totale,
SUM(nucleaire) / SUM(production) AS pct_nucleaire,
SUM(fioul + charbon + gaz) / SUM(production) AS pct_thermique,
SUM(eolien + solaire + hydraulique + bioenergies) / SUM(production) AS pct_renouvelable,
SUM(taux_co2 * production) / SUM(production) AS taux_co2
from {{ref('nat_cons_agre_j')}}
