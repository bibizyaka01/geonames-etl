"""Run inside a configured worker after a successful lite load."""

import os
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import psycopg

from geonames_etl.initial import replace_dataset


@unittest.skipUnless(os.environ.get("AIRFLOW_CONN_GEONAMES_DWH"), "Needs running DWH")
class InitialRollbackTests(unittest.TestCase):
    def snapshot(self):
        with psycopg.connect(os.environ["AIRFLOW_CONN_GEONAMES_DWH"]) as connection:
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
                with psycopg.connect(os.environ["AIRFLOW_CONN_GEONAMES_DWH"]) as connection:
                    replace_dataset(connection, archive, "lite")
        self.assertEqual(self.snapshot(), before)

    def test_invalid_integer_rolls_back_staging_and_core(self):
        self.assert_rollback("\t".join(["not-an-integer", "Invalid"] + [""] * 17) + "\n", psycopg.DataError)

    def test_empty_archive_preserves_previous_dataset(self):
        self.assert_rollback("", ValueError)


if __name__ == "__main__":
    unittest.main()
