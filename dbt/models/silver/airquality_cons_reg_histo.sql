{{ config(
    alias='airquality_cons_reg_histo',
) }}

with airqual_paris as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_paris')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_paris')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_dif = B.last_dif AND A.date_maj = B.last_maj
    ORDER BY date_ech ASC
),

airqual_lille as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_lille')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_lille')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_dijon as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_dijon')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_dijon')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_rennes as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_rennes')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_rennes')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_orleans as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_orleans')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_orleans')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_strasbourg as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_strasbourg')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_strasbourg')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_caen as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_caen')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_caen')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_bordeaux as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_bordeaux')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_bordeaux')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_toulouse as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_toulouse')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_toulouse')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_marseille as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_marseille')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_marseille')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

airqual_nantes as (
    SELECT A.insee_code,
           A.code_zone,
           A.date_maj,
           A.date_ech,
           A.date_dif,
           A.code_qual,
           A.code_no2,
           A.code_so2,
           A.code_o3,
           A.code_pm10,
           A.code_pm25
    FROM {{ref('stg_air_quality_nantes')}} AS A
    INNER JOIN (
        SELECT date_ech, code_zone, MAX(date_maj) AS last_maj, MAX(date_dif) AS last_dif
        FROM {{ref('stg_air_quality_nantes')}}
        GROUP BY code_zone, date_ech
    ) AS B
    ON A.code_zone = B.code_zone AND A.date_ech = B.date_ech AND A.date_maj = B.last_maj AND A.date_dif = B.last_dif
    ORDER BY date_ech ASC
),

final as (
    SELECT * FROM airqual_paris
    UNION ALL
    SELECT * FROM airqual_lille
    UNION ALL
    SELECT * FROM airqual_dijon
    UNION ALL
    SELECT * FROM airqual_rennes
    UNION ALL
    SELECT * FROM airqual_orleans
    UNION ALL
    SELECT * FROM airqual_strasbourg
    UNION ALL
    SELECT * FROM airqual_caen
    UNION ALL
    SELECT * FROM airqual_bordeaux
    UNION ALL
    SELECT * FROM airqual_toulouse
    UNION ALL
    SELECT * FROM airqual_marseille
    UNION ALL
    SELECT * FROM airqual_nantes
)

SELECT * FROM final
