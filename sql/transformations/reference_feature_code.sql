-- Executed inside the same transaction as staging COPY.
TRUNCATE core.feature_code;
INSERT INTO core.feature_code (code, name, description)
SELECT
    NULLIF(code, ''),
    NULLIF(name, ''),
    NULLIF(description, '')
FROM stg.feature_code;

