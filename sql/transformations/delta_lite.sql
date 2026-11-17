INSERT INTO core.geoname (geonameid, name, asciiname, alternatenames, latitude, longitude, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date)
SELECT
    NULLIF(geonameid, '')::bigint,
    NULLIF(name, ''),
    NULLIF(asciiname, ''),
    NULLIF(alternatenames, ''),
    NULLIF(latitude, '')::double precision,
    NULLIF(longitude, '')::double precision,
    NULLIF(feature_class, ''),
    NULLIF(feature_code, ''),
    NULLIF(country_code, ''),
    NULLIF(cc2, ''),
    NULLIF(admin1_code, ''),
    NULLIF(admin2_code, ''),
    NULLIF(admin3_code, ''),
    NULLIF(admin4_code, ''),
    NULLIF(population, '')::bigint,
    NULLIF(elevation, '')::integer,
    NULLIF(dem, '')::integer,
    NULLIF(timezone, ''),
    NULLIF(modification_date, '')::date
FROM stg.delta_geoname d
WHERE true AND EXISTS (SELECT 1 FROM core.geoname g WHERE g.geonameid=d.geonameid::bigint)
ON CONFLICT (geonameid) DO UPDATE SET
    name=excluded.name,
    asciiname=excluded.asciiname,
    alternatenames=excluded.alternatenames,
    latitude=excluded.latitude,
    longitude=excluded.longitude,
    feature_class=excluded.feature_class,
    feature_code=excluded.feature_code,
    country_code=excluded.country_code,
    cc2=excluded.cc2,
    admin1_code=excluded.admin1_code,
    admin2_code=excluded.admin2_code,
    admin3_code=excluded.admin3_code,
    admin4_code=excluded.admin4_code,
    population=excluded.population,
    elevation=excluded.elevation,
    dem=excluded.dem,
    timezone=excluded.timezone,
    modification_date=excluded.modification_date;

