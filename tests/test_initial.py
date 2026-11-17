import tempfile
import unittest
from datetime import date
from pathlib import Path
from zipfile import ZipFile
from zoneinfo import ZoneInfo

from geonames_etl.initial import iter_geonames, parse_source_date


class SnapshotDateTests(unittest.TestCase):
    def test_source_day_uses_central_european_timezone(self):
        modified = parse_source_date("Mon, 16 Nov 2026 23:30:00 GMT")
        self.assertEqual(modified.astimezone(ZoneInfo("Europe/Berlin")).date(), date(2026, 11, 17))

    def test_missing_invalid_and_naive_headers_rejected(self):
        for value in (None, "bad date", "Tue, 17 Nov 2026 03:00:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_source_date(value)


class InitialArchiveTests(unittest.TestCase):
    def test_stream_preserves_empty_fields_and_unicode(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.zip"
            fields = ["1", "Москва", "", '"quoted"\\name'] + [""] * 15
            with ZipFile(path, "w") as archive:
                archive.writestr("cities15000.txt", "\t".join(fields) + "\n")
            self.assertEqual(list(iter_geonames(path, "cities15000.txt")), [fields])
            self.assertEqual([item.name for item in Path(folder).iterdir()], ["data.zip"])

    def test_malformed_record_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("cities15000.txt", "1\tbad\n")
            with self.assertRaisesRegex(ValueError, "expected 19 columns"):
                list(iter_geonames(path, "cities15000.txt"))

    def test_missing_expected_member_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("unexpected.txt", "irrelevant")
            with self.assertRaises(KeyError):
                list(iter_geonames(path, "cities15000.txt"))
