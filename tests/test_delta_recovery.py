import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from geonames_etl.delta import recover_deltas


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.previous = date(2026, 11, 16)
        self.applied = []
        self.connect = MagicMock()
        self.connect.return_value.__enter__.return_value.execute.return_value.fetchone.side_effect = (
            lambda: ("full", self.previous, date(2026, 11, 17))
        )
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def apply(self, connection, day, mode, modifications, deletes):
        self.assertEqual(day.toordinal(), self.previous.toordinal() + 1)
        self.previous = day
        self.applied.append(day.day)
        return {"changed": 2, "deleted": 1}

    def recover(self):
        return recover_deltas(self.connect, date(2026, 11, 20), "full", Path(self.directory.name))

    def test_all_missing_days_then_repeat_without_downloads(self):
        with patch("geonames_etl.delta.download_delta") as download, patch(
            "geonames_etl.delta.apply_delta", side_effect=self.apply
        ):
            result = self.recover()
            self.assertEqual(self.applied, [17, 18, 19, 20])
            self.assertEqual(result["days_processed"], 4)
            self.assertEqual(download.call_count, 8)
            self.assertEqual(self.recover()["days_processed"], 0)
            self.assertEqual(download.call_count, 8)

    def test_failure_resumes_from_last_successful_day(self):
        def fail_on_18(connection, day, *args):
            if day.day == 18:
                raise RuntimeError("Interrupted")
            return self.apply(connection, day, *args)

        with patch("geonames_etl.delta.download_delta"), patch(
            "geonames_etl.delta.apply_delta", side_effect=fail_on_18
        ), self.assertRaises(RuntimeError):
            self.recover()
        self.assertEqual(self.previous.day, 17)
        with patch("geonames_etl.delta.download_delta"), patch(
            "geonames_etl.delta.apply_delta", side_effect=self.apply
        ):
            self.recover()
        self.assertEqual(self.applied, [17, 18, 19, 20])

    def test_missing_file_does_not_advance_watermark(self):
        with patch("geonames_etl.delta.download_delta", side_effect=ValueError("Missing delta")), patch(
            "geonames_etl.delta.apply_delta"
        ) as apply:
            with self.assertRaisesRegex(ValueError, "Missing delta"):
                self.recover()
        apply.assert_not_called()
        self.assertEqual(self.previous, date(2026, 11, 16))
