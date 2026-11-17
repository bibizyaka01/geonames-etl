-- Executed inside the same transaction as staging COPY.
TRUNCATE core.country;
INSERT INTO core.country (country_code, iso3, iso_numeric, fips, name, capital, area_sq_km, population, continent_code, tld, currency_code, currency_name, phone, postal_code_format, postal_code_regex, languages, geonameid, neighbours, equivalent_fips_code)
SELECT
    NULLIF(country_code, ''),
    NULLIF(iso3, ''),
    NULLIF(iso_numeric, ''),
    NULLIF(fips, ''),
    NULLIF(name, ''),
    NULLIF(capital, ''),
    NULLIF(area_sq_km, '')::numeric,
    NULLIF(population, '')::bigint,
    NULLIF(continent_code, ''),
    NULLIF(tld, ''),
    NULLIF(currency_code, ''),
    NULLIF(currency_name, ''),
    NULLIF(phone, ''),
    NULLIF(postal_code_format, ''),
    NULLIF(postal_code_regex, ''),
    NULLIF(languages, ''),
    NULLIF(geonameid, '')::bigint,
    NULLIF(neighbours, ''),
    NULLIF(equivalent_fips_code, '')
FROM stg.country;

