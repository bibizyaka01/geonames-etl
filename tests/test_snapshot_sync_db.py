"""Reconciliation checks in a dedicated disposable database, never main DWH."""

import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import psycopg

from geonames_etl.initial import replace_dataset


@unittest.skipUnless(os.environ.get("SNAPSHOT_TEST_DATABASE"), "Needs isolated snapshot test DB")
class SnapshotSyncTests(unittest.TestCase):
    def setUp(self):
        database = os.environ["SNAPSHOT_TEST_DATABASE"]
        if not database.startswith("geonames_snapshot_tests_"):
            raise ValueError("Refusing to test against a non-test database")
        self.connection = psycopg.connect(os.environ["AIRFLOW_CONN_GEONAMES_DWH"], dbname=database)
        self.addCleanup(self.connection.close)
        self.addCleanup(self.connection.rollback)
        self.connection.execute("TRUNCATE core.geoname,core.dataset_state,stg.geoname")
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    @staticmethod
    def row(identifier, population):
        return "\t".join([str(identifier), f"City {identifier}", "", "", "0", "0", "P", "PPL",
                          "ZZ", "", "", "", "", "", str(population), "", "", "UTC", "2020-01-01"]) + "\n"

    def sync(self, rows, day=21):
        path = Path(self.directory.name) / "snapshot.zip"
        with ZipFile(path, "w") as archive:
            archive.writestr("cities15000.txt", "".join(self.row(*row) for row in rows))
        return replace_dataset(self.connection, path, "lite", datetime(2026, 11, day, tzinfo=timezone.utc))

    def versions(self):
        return dict(self.connection.execute("SELECT geonameid,ctid::text FROM core.geoname"))

    def test_insert_update_delete_unchanged_and_repeat(self):
        self.sync([(1, 10), (2, 20), (3, 30)], day=20)
        self.connection.commit()
        before = self.versions()
        self.assertEqual(self.sync([(1, 10), (2, 21), (4, 40)]), 3)
        after = self.versions()
        self.assertEqual(after[1], before[1])
        self.assertNotEqual(after[2], before[2])
        self.assertEqual(set(after), {1, 2, 4})
        self.connection.commit()
        self.sync([(1, 10), (2, 21), (4, 40)])
        self.assertEqual(self.versions(), after)

    def test_duplicate_snapshot_does_not_change_core(self):
        self.sync([(1, 10)])
        before = self.versions()
        with self.assertRaises(psycopg.errors.UniqueViolation):
            with self.connection.transaction():
                self.sync([(2, 20), (2, 21)])
        self.assertEqual(self.versions(), before)

    def test_snapshot_older_than_delta_rejected(self):
        self.sync([(1, 10)], day=20)
        self.connection.execute("UPDATE core.dataset_state SET last_delta_date='2026-11-20'")
        with self.assertRaisesRegex(ValueError, "latest applied delta"):
            self.sync([(2, 20)], day=20)
        self.assertEqual(set(self.versions()), {1})
