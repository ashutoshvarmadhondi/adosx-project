import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from reconciliation.models import ReasonCode

RECORD_REF_PATTERN = re.compile(
    r"^(?:REC[\s_-]*)?(\d+)$",
    re.IGNORECASE,
)

SYSTEM_A_REQUIRED_COLUMNS = {
    "record_id",
    "location_id",
    "event_date",
    "category_code",
    "actor_id",
    "base_value",
    "adjustment",
    "total_value",
    "state",
}

SYSTEM_B_REQUIRED_COLUMNS = {
    "entry_id",
    "record_ref",
    "location_id",
    "recorded_on",
    "value",
    "label",
}


@dataclass(frozen=True)
class ReconciliationFinding:
    record_id: str
    reason_code: str
    reason: str
    system_a_record_id: str
    system_b_entry_ids: list[str]
    evidence: dict[str, Any]


def system_b_entries_are_exact_duplicates(
    entries: list[SystemBEntry],
) -> bool:
    if len(entries) < 2:
        return False

    first = entries[0]

    return all(
        entry.record_ref == first.record_ref
        and entry.location_id == first.location_id
        and entry.recorded_on == first.recorded_on
        and entry.value == first.value
        and entry.label == first.label
        for entry in entries[1:]
    )


def reconcile_records(
    system_a_records: list[SystemARecord],
    system_b_entries: list[SystemBEntry],
) -> list[ReconciliationFinding]:
    findings: list[ReconciliationFinding] = []

    system_a_by_id = {
        record.record_id: record
        for record in system_a_records
        if record.record_id is not None
    }

    grouped_system_b, invalid_system_b_entries = group_system_b_entries(
        system_b_entries
    )

    for entry in invalid_system_b_entries:
        reason_code = (
            ReasonCode.MISSING_SYSTEM_B_REFERENCE
            if not entry.raw_record_ref
            else ReasonCode.INVALID_SYSTEM_B_REFERENCE
        )

        findings.append(
            ReconciliationFinding(
                record_id=f"SYSTEM-B-ROW-{entry.row_number}",
                reason_code=reason_code,
                reason=ReasonCode(reason_code).label,
                system_a_record_id="",
                system_b_entry_ids=[entry.entry_id],
                evidence={
                    "system_b_row_number": entry.row_number,
                    "raw_record_ref": entry.raw_record_ref,
                },
            )
        )

    system_a_ids = set(system_a_by_id)
    system_b_ids = set(grouped_system_b)

    for record_id in sorted(system_a_ids - system_b_ids):
        record = system_a_by_id[record_id]

        findings.append(
            ReconciliationFinding(
                record_id=record_id,
                reason_code=ReasonCode.MISSING_IN_SYSTEM_B,
                reason=ReasonCode.MISSING_IN_SYSTEM_B.label,
                system_a_record_id=record_id,
                system_b_entry_ids=[],
                evidence={
                    "system_a_row_number": record.row_number,
                    "system_a_location_id": record.location_id,
                },
            )
        )

    for record_id in sorted(system_b_ids - system_a_ids):
        entries = grouped_system_b[record_id]

        findings.append(
            ReconciliationFinding(
                record_id=record_id,
                reason_code=ReasonCode.MISSING_IN_SYSTEM_A,
                reason=ReasonCode.MISSING_IN_SYSTEM_A.label,
                system_a_record_id="",
                system_b_entry_ids=[
                    entry.entry_id for entry in entries
                ],
                evidence={
                    "system_b_rows": [
                        entry.row_number for entry in entries
                    ],
                    "system_b_location_ids": sorted(
                        {entry.location_id for entry in entries}
                    ),
                },
            )
        )

    for record_id in sorted(system_a_ids & system_b_ids):
        system_a = system_a_by_id[record_id]
        entries = grouped_system_b[record_id]

        entry_ids = [entry.entry_id for entry in entries]

        if system_b_entries_are_exact_duplicates(entries):
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.DUPLICATE_SYSTEM_B_ENTRY,
                    reason=ReasonCode.DUPLICATE_SYSTEM_B_ENTRY.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={
                        "system_a_total_value": str(
                            system_a.total_value
                        ),
                        "system_b_values": [
                            str(entry.value) for entry in entries
                        ],
                        "system_b_rows": [
                            entry.row_number for entry in entries
                        ],
                    },
                )
            )
            continue

        missing_b_values = [
            entry for entry in entries if entry.value is None
        ]

        if missing_b_values:
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.MISSING_SYSTEM_B_VALUE,
                    reason=ReasonCode.MISSING_SYSTEM_B_VALUE.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={
                        "system_b_rows": [
                            entry.row_number
                            for entry in missing_b_values
                        ],
                    },
                )
            )
        elif system_a.total_value is None:
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.MISSING_SYSTEM_A_VALUE,
                    reason=ReasonCode.MISSING_SYSTEM_A_VALUE.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={
                        "system_a_row_number": system_a.row_number,
                    },
                )
            )
        else:
            system_b_total = sum(
                entry.value
                for entry in entries
                if entry.value is not None
            )

            if system_b_total != system_a.total_value:
                findings.append(
                    ReconciliationFinding(
                        record_id=record_id,
                        reason_code=ReasonCode.VALUE_MISMATCH,
                        reason=ReasonCode.VALUE_MISMATCH.label,
                        system_a_record_id=record_id,
                        system_b_entry_ids=entry_ids,
                        evidence={
                            "system_a_total_value": str(
                                system_a.total_value
                            ),
                            "system_b_total_value": str(
                                system_b_total
                            ),
                            "system_b_values": [
                                str(entry.value)
                                for entry in entries
                            ],
                        },
                    )
                )

        system_b_locations = {
            entry.location_id
            for entry in entries
            if entry.location_id
        }

        if not system_a.location_id:
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.MISSING_SYSTEM_A_LOCATION,
                    reason=ReasonCode.MISSING_SYSTEM_A_LOCATION.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={},
                )
            )
        elif any(
            entry.location_id == ""
            for entry in entries
        ):
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.MISSING_SYSTEM_B_LOCATION,
                    reason=ReasonCode.MISSING_SYSTEM_B_LOCATION.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={
                        "system_b_rows": [
                            entry.row_number
                            for entry in entries
                            if not entry.location_id
                        ],
                    },
                )
            )
        elif system_b_locations != {system_a.location_id}:
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.LOCATION_MISMATCH,
                    reason=ReasonCode.LOCATION_MISMATCH.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={
                        "system_a_location_id": system_a.location_id,
                        "system_b_location_ids": sorted(
                            system_b_locations
                        ),
                    },
                )
            )

        system_b_dates = {
            entry.recorded_on
            for entry in entries
            if entry.recorded_on is not None
        }

        if system_a.event_date is None:
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.MISSING_SYSTEM_A_DATE,
                    reason=ReasonCode.MISSING_SYSTEM_A_DATE.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={},
                )
            )
        elif any(
            entry.recorded_on is None
            for entry in entries
        ):
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.MISSING_SYSTEM_B_DATE,
                    reason=ReasonCode.MISSING_SYSTEM_B_DATE.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={
                        "system_b_rows": [
                            entry.row_number
                            for entry in entries
                            if entry.recorded_on is None
                        ],
                    },
                )
            )
        elif system_b_dates != {system_a.event_date}:
            findings.append(
                ReconciliationFinding(
                    record_id=record_id,
                    reason_code=ReasonCode.DATE_MISMATCH,
                    reason=ReasonCode.DATE_MISMATCH.label,
                    system_a_record_id=record_id,
                    system_b_entry_ids=entry_ids,
                    evidence={
                        "system_a_event_date": (
                            system_a.event_date.isoformat()
                        ),
                        "system_b_recorded_dates": sorted(
                            value.isoformat()
                            for value in system_b_dates
                        ),
                    },
                )
            )

    return findings


class CSVValidationError(ValueError):
    """Raised when a CSV file is missing required columns."""


@dataclass(frozen=True)
class SystemARecord:
    row_number: int
    raw_record_id: str
    record_id: str | None
    location_id: str
    event_date: date | None
    category_code: str
    actor_id: str
    base_value: Decimal | None
    adjustment: Decimal | None
    total_value: Decimal | None
    state: str


@dataclass(frozen=True)
class SystemBEntry:
    row_number: int
    entry_id: str
    raw_record_ref: str
    record_ref: str | None
    location_id: str
    recorded_on: date | None
    value: Decimal | None
    label: str


def normalize_record_ref(value: Any) -> str | None:
    """
    Normalize record references into REC-<number> format.

    Examples:
        REC-1001 -> REC-1001
        rec1001  -> REC-1001
        REC 1001 -> REC-1001
        1001     -> REC-1001
    """
    if value is None:
        return None

    cleaned = str(value).strip()

    if not cleaned:
        return None

    match = RECORD_REF_PATTERN.fullmatch(cleaned)

    if not match:
        return None

    return f"REC-{match.group(1)}"


def parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None

    cleaned = str(value).strip().replace(",", "")

    if not cleaned:
        return None

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_date(value: Any) -> date | None:
    if value is None:
        return None

    cleaned = str(value).strip()

    if not cleaned:
        return None

    supported_formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d/%m/%y",
    )

    for date_format in supported_formats:
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue

    return None


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def validate_csv_columns(
    fieldnames: list[str] | None,
    required_columns: set[str],
    source_name: str,
) -> None:
    actual_columns = set(fieldnames or [])
    missing_columns = required_columns - actual_columns

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise CSVValidationError(
            f"{source_name} is missing required columns: {missing}"
        )


def load_system_a_csv(csv_path: str | Path) -> list[SystemARecord]:
    path = Path(csv_path)
    records: list[SystemARecord] = []

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        validate_csv_columns(
            reader.fieldnames,
            SYSTEM_A_REQUIRED_COLUMNS,
            "System A CSV",
        )

        for row_number, row in enumerate(reader, start=2):
            raw_record_id = clean_text(row.get("record_id"))

            records.append(
                SystemARecord(
                    row_number=row_number,
                    raw_record_id=raw_record_id,
                    record_id=normalize_record_ref(raw_record_id),
                    location_id=clean_text(row.get("location_id")).upper(),
                    event_date=parse_date(row.get("event_date")),
                    category_code=clean_text(
                        row.get("category_code")
                    ).upper(),
                    actor_id=clean_text(row.get("actor_id")).upper(),
                    base_value=parse_decimal(row.get("base_value")),
                    adjustment=parse_decimal(row.get("adjustment")),
                    total_value=parse_decimal(row.get("total_value")),
                    state=clean_text(row.get("state")).upper(),
                )
            )

    return records


def load_system_b_csv(csv_path: str | Path) -> list[SystemBEntry]:
    path = Path(csv_path)
    entries: list[SystemBEntry] = []

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        validate_csv_columns(
            reader.fieldnames,
            SYSTEM_B_REQUIRED_COLUMNS,
            "System B CSV",
        )

        for row_number, row in enumerate(reader, start=2):
            raw_record_ref = clean_text(row.get("record_ref"))

            entries.append(
                SystemBEntry(
                    row_number=row_number,
                    entry_id=clean_text(row.get("entry_id")),
                    raw_record_ref=raw_record_ref,
                    record_ref=normalize_record_ref(raw_record_ref),
                    location_id=clean_text(row.get("location_id")).upper(),
                    recorded_on=parse_date(row.get("recorded_on")),
                    value=parse_decimal(row.get("value")),
                    label=clean_text(row.get("label")),
                )
            )

    return entries


def group_system_b_entries(
    entries: list[SystemBEntry],
) -> tuple[dict[str, list[SystemBEntry]], list[SystemBEntry]]:
    """
    Group valid System B entries by normalized record reference.

    Entries with missing or invalid references are returned separately so
    reconciliation can create appropriate validation exceptions later.
    """
    grouped_entries: defaultdict[str, list[SystemBEntry]] = defaultdict(list)
    invalid_reference_entries: list[SystemBEntry] = []

    for entry in entries:
        if entry.record_ref is None:
            invalid_reference_entries.append(entry)
            continue

        grouped_entries[entry.record_ref].append(entry)

    return dict(grouped_entries), invalid_reference_entries
