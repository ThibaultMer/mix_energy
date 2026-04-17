SELECT aasqa as insee_code,
        date_maj,
        date_ech,
        date_dif,
        code_qual,
        CAST(code_zone AS INT64) AS code_zone,
        code_no2,
        code_so2,
        code_o3,
        code_pm10,
        code_pm25
FROM {{source('airqual_source','air_quality_lyon')}}
WHERE code_zone = "69123"
ORDER BY date_maj DESC
