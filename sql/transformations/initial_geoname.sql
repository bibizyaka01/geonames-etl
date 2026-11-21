-- Validate the entire typed snapshot before changing core.
DROP TABLE IF EXISTS pg_temp.incoming_geoname;
CREATE TEMP TABLE incoming_geoname (geonameid, name, asciiname, alternatenames, latitude, longitude, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date) ON COMMIT DROP AS
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
ALTER TABLE incoming_geoname ADD PRIMARY KEY (geonameid);
ANALYZE incoming_geoname;

-- Filter before upsert so unchanged records are not locked or rewritten.
INSERT INTO core.geoname AS target (geonameid, name, asciiname, alternatenames, latitude, longitude, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date)
SELECT s.geonameid, s.name, s.asciiname, s.alternatenames, s.latitude, s.longitude, s.feature_class, s.feature_code, s.country_code, s.cc2, s.admin1_code, s.admin2_code, s.admin3_code, s.admin4_code, s.population, s.elevation, s.dem, s.timezone, s.modification_date
FROM incoming_geoname s
LEFT JOIN core.geoname existing USING (geonameid)
WHERE existing.geonameid IS NULL
   OR ROW(existing.name, existing.asciiname, existing.alternatenames, existing.latitude, existing.longitude, existing.feature_class, existing.feature_code, existing.country_code, existing.cc2, existing.admin1_code, existing.admin2_code, existing.admin3_code, existing.admin4_code, existing.population, existing.elevation, existing.dem, existing.timezone, existing.modification_date) IS DISTINCT FROM ROW(s.name, s.asciiname, s.alternatenames, s.latitude, s.longitude, s.feature_class, s.feature_code, s.country_code, s.cc2, s.admin1_code, s.admin2_code, s.admin3_code, s.admin4_code, s.population, s.elevation, s.dem, s.timezone, s.modification_date)
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
    modification_date=excluded.modification_date
WHERE ROW(target.name, target.asciiname, target.alternatenames, target.latitude, target.longitude, target.feature_class, target.feature_code, target.country_code, target.cc2, target.admin1_code, target.admin2_code, target.admin3_code, target.admin4_code, target.population, target.elevation, target.dem, target.timezone, target.modification_date) IS DISTINCT FROM ROW(excluded.name, excluded.asciiname, excluded.alternatenames, excluded.latitude, excluded.longitude, excluded.feature_class, excluded.feature_code, excluded.country_code, excluded.cc2, excluded.admin1_code, excluded.admin2_code, excluded.admin3_code, excluded.admin4_code, excluded.population, excluded.elevation, excluded.dem, excluded.timezone, excluded.modification_date);

DELETE FROM core.geoname g
WHERE NOT EXISTS (SELECT 1 FROM incoming_geoname s WHERE s.geonameid=g.geonameid);

