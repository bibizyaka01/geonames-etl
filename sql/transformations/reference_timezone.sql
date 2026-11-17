-- Executed inside the same transaction as staging COPY.
TRUNCATE core.timezone;
INSERT INTO core.timezone (country_code, timezone_id, gmt_offset, dst_offset, raw_offset)
SELECT
    NULLIF(country_code, ''),
    NULLIF(timezone_id, ''),
    NULLIF(gmt_offset, '')::numeric,
    NULLIF(dst_offset, '')::numeric,
    NULLIF(raw_offset, '')::numeric
FROM stg.timezone;

