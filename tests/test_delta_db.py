"""Synthetic delta checks; all fixture changes are rolled back."""

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

import psycopg

from geonames_etl.delta import apply_delta


@unittest.skipUnless(os.environ.get("AIRFLOW_CONN_GEONAMES_DWH"), "Needs running DWH")
class DeltaTests(unittest.TestCase):
    def setUp(self):
        self.connection = psycopg.connect(os.environ["AIRFLOW_CONN_GEONAMES_DWH"])
        self.addCleanup(self.connection.close)
        self.addCleanup(self.connection.rollback)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.modifications = Path(self.directory.name) / "modifications.txt"
        self.deletes = Path(self.directory.name) / "deletes.txt"
        self.connection.execute("SELECT pg_advisory_xact_lock(hashtext('geonames.geoname'))")
        self.connection.execute("DELETE FROM core.geoname")
        self.connection.execute("INSERT INTO core.geoname (geonameid,name) VALUES (1,'Original')")
        self.connection.execute(
            "UPDATE core.dataset_state SET mode='full', loaded_at='2026-11-17 12:00:00+00', "
            "last_delta_date=NULL, row_count=1 WHERE dataset='geoname'"
        )
        self.modifications.write_text(self.row(1, "Updated") + self.row(2, "New"))
        self.deletes.write_text("")

    @staticmethod
    def row(identifier, name):
        return "\t".join([str(identifier), name, "", "", "0", "0", "P", "PPL", "ZZ",
                          "", "", "", "", "", "20000", "", "", "UTC", "2026-11-17"]) + "\n"

    def rows(self):
        return self.connection.execute("SELECT geonameid,name FROM core.geoname ORDER BY 1").fetchall()

    def test_full_upsert_delete_and_repeat(self):
        self.deletes.write_text("1\tOriginal\tdeleted\n")
        apply_delta(self.connection, date(2026, 11, 18), "full", self.modifications, self.deletes)
        self.assertEqual(self.rows(), [(2, "New")])
        result = apply_delta(self.connection, date(2026, 11, 18), "full", self.modifications, self.deletes)
        self.assertEqual(result["status"], "already_processed")
        self.assertEqual(self.rows(), [(2, "New")])

    def test_lite_updates_only_existing_ids(self):
        self.connection.execute("UPDATE core.dataset_state SET mode='lite' WHERE dataset='geoname'")
        apply_delta(self.connection, date(2026, 11, 18), "lite", self.modifications, self.deletes)
        self.assertEqual(self.rows(), [(1, "Updated")])

    def test_gap_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing delta"):
            apply_delta(self.connection, date(2026, 11, 19), "full", self.modifications, self.deletes)
        self.assertEqual(self.rows(), [(1, "Original")])

    def test_bad_deletion_rolls_back_upsert_and_watermark(self):
        self.deletes.write_text("not-a-number\tInvalid\tdeleted\n")
        with self.assertRaises(psycopg.DataError):
            with self.connection.transaction():
                apply_delta(self.connection, date(2026, 11, 18), "full", self.modifications, self.deletes)
        self.assertEqual(self.rows(), [(1, "Original")])
        self.assertIsNone(self.connection.execute(
            "SELECT last_delta_date FROM core.dataset_state WHERE dataset='geoname'"
        ).fetchone()[0])


if __name__ == "__main__":
    unittest.main()
