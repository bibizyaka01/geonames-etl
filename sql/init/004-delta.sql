BEGIN;
CREATE TABLE IF NOT EXISTS stg.delta_geoname (LIKE stg.geoname);
CREATE TABLE IF NOT EXISTS stg.delta_deletes (
    geonameid text,
    name text,
    comment text
);
ALTER TABLE core.dataset_state ADD COLUMN IF NOT EXISTS last_delta_date date;
COMMIT;
