{{ config(
    alias='meteo_cons_reg_histo',
) }}

with meteo_paris as (
    SELECT
    11 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_paris')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_lyon as (
    SELECT
    84 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_lyon')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_lille as (
    SELECT
    32 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_lille')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_dijon as (
    SELECT
    27 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_dijon')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_rennes as (
    SELECT
    53 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_rennes')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_orleans as (
    SELECT
    24 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_orleans')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_strasbourg as (
    SELECT
    44 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_strasbourg')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_caen as (
    SELECT
    28 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_caen')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_bordeaux as (
    SELECT
    75 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_bordeaux')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_toulouse as (
    SELECT
    761 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_toulouse')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_marseille as (
    SELECT
    93 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_marseille')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

meteo_nantes as (
    SELECT
    52 AS insee_region,
    date_m,
    day_time,
    ROUND(mean_temp_2m,2) AS mean_temp_2m,
    ROUND(mean_rel_hum_2m,2) AS mean_rel_hum_2m,
    ROUND(mean_wind_speed_10m,2) AS mean_wind_speed_10m,
    ROUND(mean_evapo,2) AS mean_evapo
    FROM {{ref('stg_meteo_nantes')}}
    GROUP BY date_m,day_time,mean_temp_2m,mean_rel_hum_2m,mean_wind_speed_10m,mean_evapo
    HAVING COUNT(*) > 1
),

final AS (
SELECT * FROM meteo_paris
UNION ALL
SELECT * FROM meteo_lyon
UNION ALL
SELECT * FROM meteo_lille
UNION ALL
SELECT * FROM meteo_dijon
UNION ALL
SELECT * FROM meteo_rennes
UNION ALL
SELECT * FROM meteo_orleans
UNION ALL
SELECT * FROM meteo_strasbourg
UNION ALL
SELECT * FROM meteo_caen
UNION ALL
SELECT * FROM meteo_bordeaux
UNION ALL
SELECT * FROM meteo_toulouse
UNION ALL
SELECT * FROM meteo_marseille
UNION ALL
SELECT * FROM meteo_nantes
)

SELECT * FROM final
