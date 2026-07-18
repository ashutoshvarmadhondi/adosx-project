from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from reconciliation.models import ReasonCode
from reconciliation.services import reconcile_records
from reconciliation.services import (
    CSVValidationError,
    group_system_b_entries,
    load_system_a_csv,
    load_system_b_csv,
    normalize_record_ref,
    parse_date,
    parse_decimal,
)


class ReconciliationEngineTest(SimpleTestCase):
    def test_detects_duplicate_and_accepts_valid_split(self):
        system_a_csv = (
            "record_id,location_id,event_date,category_code,actor_id,"
            "base_value,adjustment,total_value,state\n"
            "REC-1042,LOC-101,2026-03-04,CAT-02,USR-11,"
            "100,10,112837.06,CONFIRMED\n"
            "REC-1055,LOC-103,2026-03-14,CAT-08,USR-11,"
            "100,10,179877.32,CONFIRMED\n"
        )

        system_b_csv = (
            "entry_id,record_ref,location_id,recorded_on,value,label\n"
            "ENT-1,REC-1042,LOC-101,2026-03-04,"
            "112837.06,Entry for CAT-02\n"
            "ENT-2,REC-1042,LOC-101,2026-03-04,"
            "112837.06,Entry for CAT-02\n"
            "ENT-3,REC-1055,LOC-103,2026-03-14,"
            "71950.93,Entry for CAT-08\n"
            "ENT-4,REC-1055,LOC-103,2026-03-14,"
            "107926.39,Entry part 2 of 2\n"
        )

        with TemporaryDirectory() as directory:
            directory_path = Path(directory)

            system_a_path = directory_path / "system_a.csv"
            system_b_path = directory_path / "system_b.csv"

            system_a_path.write_text(
                system_a_csv,
                encoding="utf-8",
            )
            system_b_path.write_text(
                system_b_csv,
                encoding="utf-8",
            )

            findings = reconcile_records(
                load_system_a_csv(system_a_path),
                load_system_b_csv(system_b_path),
            )

        finding_pairs = {
            (finding.record_id, finding.reason_code)
            for finding in findings
        }

        self.assertIn(
            (
                "REC-1042",
                ReasonCode.DUPLICATE_SYSTEM_B_ENTRY,
            ),
            finding_pairs,
        )

        self.assertFalse(
            any(
                finding.record_id == "REC-1055"
                for finding in findings
            )
        )

    def test_detects_missing_records(self):
        system_a_csv = (
            "record_id,location_id,event_date,category_code,actor_id,"
            "base_value,adjustment,total_value,state\n"
            "REC-1015,LOC-101,2026-03-04,CAT-02,USR-11,"
            "100,10,110,CONFIRMED\n"
        )

        system_b_csv = (
            "entry_id,record_ref,location_id,recorded_on,value,label\n"
            "ENT-1,REC-1999,LOC-201,2026-03-04,110,"
            "Unmatched entry\n"
        )

        with TemporaryDirectory() as directory:
            directory_path = Path(directory)

            system_a_path = directory_path / "system_a.csv"
            system_b_path = directory_path / "system_b.csv"

            system_a_path.write_text(
                system_a_csv,
                encoding="utf-8",
            )
            system_b_path.write_text(
                system_b_csv,
                encoding="utf-8",
            )

            findings = reconcile_records(
                load_system_a_csv(system_a_path),
                load_system_b_csv(system_b_path),
            )

        finding_pairs = {
            (finding.record_id, finding.reason_code)
            for finding in findings
        }

        self.assertIn(
            ("REC-1015", ReasonCode.MISSING_IN_SYSTEM_B),
            finding_pairs,
        )
        self.assertIn(
            ("REC-1999", ReasonCode.MISSING_IN_SYSTEM_A),
            finding_pairs,
        )


class SystemACSVLoaderTest(SimpleTestCase):
    def test_loads_system_a_rows_into_typed_records(self):
        csv_content = (
            "record_id,location_id,event_date,category_code,actor_id,"
            "base_value,adjustment,total_value,state\n"
            "REC-1001,LOC-201,2026-04-03,CAT-02,USR-22,"
            "69507.75,19462.17,88969.92,CONFIRMED\n"
        )

        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "system_a.csv"
            csv_path.write_text(csv_content, encoding="utf-8")

            records = load_system_a_csv(csv_path)

        self.assertEqual(len(records), 1)

        record = records[0]

        self.assertEqual(record.row_number, 2)
        self.assertEqual(record.record_id, "REC-1001")
        self.assertEqual(record.location_id, "LOC-201")
        self.assertEqual(record.event_date, date(2026, 4, 3))
        self.assertEqual(record.total_value, Decimal("88969.92"))
        self.assertEqual(record.state, "CONFIRMED")


class SystemBCSVLoaderTest(SimpleTestCase):
    def test_loads_and_normalizes_system_b_rows(self):
        csv_content = (
            "entry_id,record_ref,location_id,recorded_on,value,label\n"
            "ENT/2026/4001, rec1001 ,LOC-201,2026-04-03,"
            "88969.92,Entry for CAT-02\n"
            "ENT/2026/4002,INVALID,LOC-201,2026-04-03,"
            "100.00,Invalid reference\n"
        )

        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "system_b.csv"
            csv_path.write_text(csv_content, encoding="utf-8")

            entries = load_system_b_csv(csv_path)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].record_ref, "REC-1001")
        self.assertIsNone(entries[1].record_ref)

    def test_groups_entries_by_normalized_record_reference(self):
        csv_content = (
            "entry_id,record_ref,location_id,recorded_on,value,label\n"
            "ENT-1,REC-1001,LOC-201,2026-04-03,400.00,Part one\n"
            "ENT-2,rec1001,LOC-201,2026-04-03,500.00,Part two\n"
            "ENT-3,BAD-REF,LOC-201,2026-04-03,100.00,Invalid\n"
        )

        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "system_b.csv"
            csv_path.write_text(csv_content, encoding="utf-8")

            entries = load_system_b_csv(csv_path)

        grouped, invalid_entries = group_system_b_entries(entries)

        self.assertEqual(list(grouped), ["REC-1001"])
        self.assertEqual(len(grouped["REC-1001"]), 2)
        self.assertEqual(len(invalid_entries), 1)
        self.assertEqual(invalid_entries[0].entry_id, "ENT-3")

    def test_rejects_csv_with_missing_columns(self):
        csv_content = "entry_id,record_ref\nENT-1,REC-1001\n"

        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "system_b.csv"
            csv_path.write_text(csv_content, encoding="utf-8")

            with self.assertRaises(CSVValidationError):
                load_system_b_csv(csv_path)


class NormalizeRecordRefTest(SimpleTestCase):
    def test_normalizes_valid_record_references(self):
        cases = {
            "REC-1001": "REC-1001",
            "rec-1001": "REC-1001",
            "REC1001": "REC-1001",
            "REC 1001": "REC-1001",
            "REC_1001": "REC-1001",
            "  REC-1001  ": "REC-1001",
            "1001": "REC-1001",
        }

        for raw_value, expected in cases.items():
            with self.subTest(raw_value=raw_value):
                self.assertEqual(
                    normalize_record_ref(raw_value),
                    expected,
                )

    def test_returns_none_for_missing_or_invalid_reference(self):
        invalid_values = [
            None,
            "",
            "   ",
            "ABC-1001",
            "REC-ABC",
            "1001-EXTRA",
        ]

        for raw_value in invalid_values:
            with self.subTest(raw_value=raw_value):
                self.assertIsNone(normalize_record_ref(raw_value))


class ParseDecimalTest(SimpleTestCase):
    def test_parses_decimal_values(self):
        cases = {
            "88969.92": Decimal("88969.92"),
            "1,21,388.01": Decimal("121388.01"),
            " 37878.21 ": Decimal("37878.21"),
            100: Decimal("100"),
        }

        for raw_value, expected in cases.items():
            with self.subTest(raw_value=raw_value):
                self.assertEqual(parse_decimal(raw_value), expected)

    def test_returns_none_for_invalid_decimal(self):
        for raw_value in [None, "", " ", "not-a-number"]:
            with self.subTest(raw_value=raw_value):
                self.assertIsNone(parse_decimal(raw_value))


class ParseDateTest(SimpleTestCase):
    def test_parses_supported_dates(self):
        cases = {
            "2026-04-03": date(2026, 4, 3),
            "03/04/2026": date(2026, 4, 3),
            "03/04/26": date(2026, 4, 3),
        }

        for raw_value, expected in cases.items():
            with self.subTest(raw_value=raw_value):
                self.assertEqual(parse_date(raw_value), expected)

    def test_returns_none_for_invalid_date(self):
        for raw_value in [None, "", "2026-15-50", "not-a-date"]:
            with self.subTest(raw_value=raw_value):
                self.assertIsNone(parse_date(raw_value))
