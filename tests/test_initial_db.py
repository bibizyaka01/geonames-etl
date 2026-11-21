"""Run inside a configured worker after a successful lite load."""

import os
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import psycopg

from geonames_etl.initial import replace_dataset


@unittest.skipUnless(os.environ.get("SNAPSHOT_TEST_DATABASE", "").startswith("geonames_snapshot_tests_"), "Needs isolated snapshot test DB")
class InitialRollbackTests(unittest.TestCase):
    def snapshot(self):
        with psycopg.connect(os.environ["AIRFLOW_CONN_GEONAMES_DWH"], dbname=os.environ["SNAPSHOT_TEST_DATABASE"]) as connection:
            core = connection.execute(
                "SELECT count(*), sum(geonameid) FROM core.geoname"
            ).fetchone()
            staging = connection.execute("SELECT count(*) FROM stg.geoname").fetchone()
        self.assertGreater(core[0], 0, "Load lite data before this integration test")
        return core, staging

    def assert_rollback(self, content, error):
        before = self.snapshot()
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "invalid.zip"
            with ZipFile(archive, "w") as zipped:
                zipped.writestr("cities15000.txt", content)
            with self.assertRaises(error):
                with psycopg.connect(os.environ["AIRFLOW_CONN_GEONAMES_DWH"], dbname=os.environ["SNAPSHOT_TEST_DATABASE"]) as connection:
                    connection.execute("UPDATE core.dataset_state SET source_last_modified=NULL,last_delta_date=NULL")
                    replace_dataset(connection, archive, "lite", datetime(2026, 11, 17, tzinfo=timezone.utc))
        self.assertEqual(self.snapshot(), before)

    def test_invalid_integer_rolls_back_staging_and_core(self):
        self.assert_rollback("\t".join(["not-an-integer", "Invalid"] + [""] * 17) + "\n", psycopg.DataError)

    def test_empty_archive_preserves_previous_dataset(self):
        self.assert_rollback("", ValueError)

    def test_success_records_source_date_independent_of_load_time(self):
        class RollbackFixture(Exception):
            pass

        before = self.snapshot()
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "fixture.zip"
            with ZipFile(archive, "w") as zipped:
                zipped.writestr("cities15000.txt", "\t".join(["1", "Fixture"] + [""] * 17) + "\n")
            try:
                with psycopg.connect(os.environ["AIRFLOW_CONN_GEONAMES_DWH"], dbname=os.environ["SNAPSHOT_TEST_DATABASE"]) as connection:
                    connection.execute("UPDATE core.dataset_state SET source_last_modified=NULL,last_delta_date=NULL")
                    modified = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
                    connection.execute("UPDATE core.dataset_state SET source_last_modified=NULL,last_delta_date=NULL")
                    replace_dataset(connection, archive, "lite", modified)
                    state = connection.execute(
                        "SELECT source_last_modified,snapshot_date,last_delta_date "
                        "FROM core.dataset_state WHERE dataset='geoname'"
                    ).fetchone()
                    self.assertEqual(state, (modified, date(2026, 11, 15), None))
                    raise RollbackFixture()
            except RollbackFixture:
                pass
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
