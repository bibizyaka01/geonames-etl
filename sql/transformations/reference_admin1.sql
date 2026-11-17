-- Executed inside the same transaction as staging COPY.
TRUNCATE core.admin1;
INSERT INTO core.admin1 (code, name, asciiname, geonameid)
SELECT
    NULLIF(code, ''),
    NULLIF(name, ''),
    NULLIF(asciiname, ''),
    NULLIF(geonameid, '')::bigint
FROM stg.admin1;

