BEGIN;
CREATE TABLE IF NOT EXISTS stg.geoname (
    geonameid text,
    name text,
    asciiname text,
    alternatenames text,
    latitude text,
    longitude text,
    feature_class text,
    feature_code text,
    country_code text,
    cc2 text,
    admin1_code text,
    admin2_code text,
    admin3_code text,
    admin4_code text,
    population text,
    elevation text,
    dem text,
    timezone text,
    modification_date text
);
CREATE TABLE IF NOT EXISTS core.geoname (
    geonameid bigint PRIMARY KEY,
    name text NOT NULL,
    asciiname text,
    alternatenames text,
    latitude double precision CHECK (latitude BETWEEN -90 AND 90),
    longitude double precision CHECK (longitude BETWEEN -180 AND 180),
    feature_class text,
    feature_code text,
    country_code text,
    cc2 text,
    admin1_code text,
    admin2_code text,
    admin3_code text,
    admin4_code text,
    population bigint,
    elevation integer,
    dem integer,
    timezone text,
    modification_date date
);
CREATE INDEX IF NOT EXISTS geoname_country_feature_idx ON core.geoname (country_code, feature_class, feature_code);
CREATE TABLE IF NOT EXISTS core.dataset_state (
    dataset text PRIMARY KEY,
    mode text NOT NULL CHECK (mode IN ('lite', 'full')),
    row_count bigint NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);
CREATE OR REPLACE VIEW mart.cities_by_country AS
SELECT g.geonameid, g.name, g.country_code, c.name AS country_name,
       g.population, g.latitude, g.longitude, g.timezone
FROM core.geoname g LEFT JOIN core.country c USING (country_code)
WHERE g.feature_class = 'P';
CREATE OR REPLACE VIEW mart.object_counts AS
SELECT feature_class, feature_code, count(*) AS object_count
FROM core.geoname GROUP BY feature_class, feature_code;
COMMIT;

