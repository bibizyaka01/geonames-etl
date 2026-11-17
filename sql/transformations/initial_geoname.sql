TRUNCATE core.geoname;
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
FROM stg.geoname;

