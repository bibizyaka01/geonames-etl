import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from geonames_etl.initial import iter_geonames


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
