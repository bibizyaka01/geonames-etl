import tempfile
import unittest
from pathlib import Path

from geonames_etl.references import iter_rows


class ReferenceParserTests(unittest.TestCase):
    def parse(self, text, reference):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.txt"
            path.write_text(text, encoding="utf-8")
            return list(iter_rows(path, reference))

    def test_preserves_quotes_backslashes_and_empty_last_field(self):
        rows = self.parse('# comment\n\nA.X\t"literal"\\name\t\n', "feature_code")
        self.assertEqual(rows, [["A.X", '"literal"\\name', ""]])

    def test_skips_timezone_header_and_accepts_fractional_offsets(self):
        rows = self.parse(
            "CountryCode\tTimeZoneId\tJanuary\tJuly\traw\n"
            "NP\tAsia/Kathmandu\t5.75\t5.75\t5.75\n", "timezone"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "5.75")

    def test_rejects_wrong_column_count(self):
        with self.assertRaisesRegex(ValueError, "expected 4 columns"):
            self.parse("XX.1\tName\tName\n", "admin1")
