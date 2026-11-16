-- GeoNames reference files: columns in source order.
-- Additive bootstrap DDL: safe to rerun; future structural changes need migrations.
BEGIN;

CREATE TABLE IF NOT EXISTS stg.country (
    country_code text,
    iso3 text,
    iso_numeric text,
    fips text,
    name text,
    capital text,
    area_sq_km text,
    population text,
    continent_code text,
    tld text,
    currency_code text,
    currency_name text,
    phone text,
    postal_code_format text,
    postal_code_regex text,
    languages text,
    geonameid text,
    neighbours text,
    equivalent_fips_code text
);

CREATE TABLE IF NOT EXISTS core.country (
    country_code text PRIMARY KEY,
    iso3 text,
    iso_numeric text,
    fips text,
    name text NOT NULL,
    capital text,
    area_sq_km numeric,
    population bigint,
    continent_code text,
    tld text,
    currency_code text,
    currency_name text,
    phone text,
    postal_code_format text,
    postal_code_regex text,
    languages text,
    geonameid bigint,
    neighbours text,
    equivalent_fips_code text
);

CREATE TABLE IF NOT EXISTS stg.admin1 (
    code text,
    name text,
    asciiname text,
    geonameid text
);

CREATE TABLE IF NOT EXISTS core.admin1 (
    code text PRIMARY KEY,
    name text NOT NULL,
    asciiname text,
    geonameid bigint
);

CREATE TABLE IF NOT EXISTS stg.feature_code (
    code text,
    name text,
    description text
);

CREATE TABLE IF NOT EXISTS core.feature_code (
    code text PRIMARY KEY,
    name text NOT NULL,
    description text
);

CREATE TABLE IF NOT EXISTS stg.timezone (
    country_code text,
    timezone_id text,
    gmt_offset text,
    dst_offset text,
    raw_offset text
);

CREATE TABLE IF NOT EXISTS core.timezone (
    country_code text NOT NULL,
    timezone_id text NOT NULL,
    gmt_offset numeric(4,2),
    dst_offset numeric(4,2),
    raw_offset numeric(4,2),
    PRIMARY KEY (country_code, timezone_id)
);

COMMENT ON COLUMN core.country.iso_numeric IS 'ISO numeric code as text to preserve leading zeros';
COMMENT ON COLUMN core.admin1.code IS 'Composite source code: country.admin1; preserve as text';
COMMENT ON COLUMN core.feature_code.code IS 'Composite source code: feature_class.feature_code';
COMMENT ON COLUMN core.timezone.gmt_offset IS 'UTC offset in hours for January of the source file year';
COMMENT ON COLUMN core.timezone.dst_offset IS 'UTC offset in hours for July of the source file year';
COMMENT ON COLUMN core.timezone.raw_offset IS 'UTC offset in hours independent of DST';

COMMIT;

