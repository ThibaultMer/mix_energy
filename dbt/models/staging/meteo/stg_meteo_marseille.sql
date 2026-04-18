SELECT
    date_m,
    day_time,
    AVG(temperature_2m) OVER (PARTITION BY date_m, day_time) AS mean_temp_2m,
    AVG(relative_humidity_2m) OVER (PARTITION BY date_m, day_time) AS mean_rel_hum_2m,
    AVG(wind_speed_10m) OVER (PARTITION BY date_m, day_time) AS mean_wind_speed_10m,
    AVG(evapotranspiration) OVER (PARTITION BY date_m, day_time) AS mean_evapo,
FROM
    (
    SELECT
        date_m,
        time_m,
        temperature_2m,
        relative_humidity_2m,
        wind_speed_10m,
        evapotranspiration,
        CASE
        WHEN time_m >= '05:00:00' AND time_m =< '12:00:00' THEN 'Morning'
        WHEN time_m > '12:00:00' AND time_m < '20:00:00' THEN 'Afternoon'
        ELSE 'Night'
        END AS day_time
    FROM
        (
        SELECT
            temperature_2m,
            relative_humidity_2m,
            wind_speed_10m,
            evapotranspiration,
            time,
            CAST(time AS date) AS date_m,
            CAST(time AS time) AS time_m,
        FROM {{source('meteo_source','meteo_marseille')}}
        )
    )
