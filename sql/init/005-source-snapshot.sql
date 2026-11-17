-- Existing snapshots deliberately remain NULL: their source date is unknown.
BEGIN;
ALTER TABLE core.dataset_state ADD COLUMN IF NOT EXISTS source_last_modified timestamptz;
ALTER TABLE core.dataset_state ADD COLUMN IF NOT EXISTS snapshot_date date;
COMMIT;
