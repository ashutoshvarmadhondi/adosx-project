import re
from dataclasses import dataclass
from typing import Iterable

from reconciliation.models import ReconciliationException, ReasonCode


RECORD_ID_PATTERN = re.compile(r"\bREC[\s_-]?(\d+)\b", re.IGNORECASE)
LOCATION_ID_PATTERN = re.compile(r"\bLOC[\s_-]?(\d+)\b", re.IGNORECASE)


REASON_KEYWORDS = {
    ReasonCode.VALUE_MISMATCH: (
        "value mismatch",
        "value mismatches",
        "amount mismatch",
        "amount mismatches",
        "different value",
        "different values",
    ),
    ReasonCode.DATE_MISMATCH: (
        "date mismatch",
        "date mismatches",
        "different date",
        "different dates",
    ),
    ReasonCode.LOCATION_MISMATCH: (
        "location mismatch",
        "location mismatches",
        "different location",
        "different locations",
    ),
    ReasonCode.MISSING_IN_SYSTEM_A: (
        "missing in system a",
        "not in system a",
    ),
    ReasonCode.MISSING_IN_SYSTEM_B: (
        "missing in system b",
        "not in system b",
    ),
    ReasonCode.DUPLICATE_SYSTEM_B_ENTRY: (
        "duplicate",
        "duplicates",
        "duplicate entry",
        "duplicate entries",
    ),
    ReasonCode.MISSING_SYSTEM_A_VALUE: (
        "missing system a value",
        "system a missing value",
    ),
    ReasonCode.MISSING_SYSTEM_B_VALUE: (
        "missing system b value",
        "system b missing value",
    ),
    ReasonCode.MISSING_SYSTEM_A_DATE: (
        "missing system a date",
        "system a missing date",
    ),
    ReasonCode.MISSING_SYSTEM_B_DATE: (
        "missing system b date",
        "system b missing date",
    ),
    ReasonCode.MISSING_SYSTEM_A_LOCATION: (
        "missing system a location",
        "system a missing location",
    ),
    ReasonCode.MISSING_SYSTEM_B_LOCATION: (
        "missing system b location",
        "system b missing location",
    ),
    ReasonCode.TENANT_MISMATCH: (
        "tenant mismatch",
        "organization mismatch",
    ),
}


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    citations: list[int]
    supported: bool


def normalize_record_id_from_question(question: str) -> str | None:
    match = RECORD_ID_PATTERN.search(question)

    if not match:
        return None

    return f"REC-{match.group(1)}"


def normalize_location_id_from_question(question: str) -> str | None:
    match = LOCATION_ID_PATTERN.search(question)

    if not match:
        return None

    return f"LOC-{match.group(1)}"


def detect_reason_code(question: str) -> str | None:
    normalized_question = question.casefold()

    for reason_code, keywords in REASON_KEYWORDS.items():
        if any(
            keyword in normalized_question
            for keyword in keywords
        ):
            return reason_code

    for choice in ReasonCode:
        readable_code = choice.value.replace("_", " ").casefold()

        if readable_code in normalized_question:
            return choice.value

    return None


def join_record_ids(record_ids: Iterable[str]) -> str:
    values = list(record_ids)

    if not values:
        return ""

    if len(values) == 1:
        return values[0]

    if len(values) == 2:
        return f"{values[0]} and {values[1]}"

    return f"{', '.join(values[:-1])}, and {values[-1]}"


def build_grounded_answer(
    question: str,
    queryset,
) -> GroundedAnswer:
    cleaned_question = question.strip()

    if not cleaned_question:
        return GroundedAnswer(
            answer="Please provide a question about reconciliation exceptions.",
            citations=[],
            supported=False,
        )

    normalized_question = cleaned_question.casefold()
    record_id = normalize_record_id_from_question(cleaned_question)
    location_id = normalize_location_id_from_question(cleaned_question)
    reason_code = detect_reason_code(cleaned_question)

    if record_id:
        rows = list(
            queryset.filter(record_id__iexact=record_id)
            .order_by("id")
        )

        if not rows:
            return GroundedAnswer(
                answer=(
                    f"No visible reconciliation exceptions were found "
                    f"for {record_id}."
                ),
                citations=[],
                supported=True,
            )

        reasons = sorted(
            {
                row.get_reason_code_display()
                for row in rows
            }
        )

        return GroundedAnswer(
            answer=(
                f"{record_id} has {len(rows)} reconciliation "
                f"exception{'s' if len(rows) != 1 else ''}: "
                f"{'; '.join(reasons)}."
            ),
            citations=[row.id for row in rows],
            supported=True,
        )

    if location_id:
        rows = list(
            queryset.filter(
                location__location_id__iexact=location_id
            ).order_by("record_id", "id")
        )

        if reason_code:
            rows = [
                row
                for row in rows
                if row.reason_code == reason_code
            ]

        if not rows:
            return GroundedAnswer(
                answer=(
                    f"No visible reconciliation exceptions were found "
                    f"for {location_id}"
                    f"{' with that reason' if reason_code else ''}."
                ),
                citations=[],
                supported=True,
            )

        record_ids = sorted(
            {row.record_id for row in rows}
        )

        reason_text = (
            f" with reason {ReasonCode(reason_code).label}"
            if reason_code
            else ""
        )

        return GroundedAnswer(
            answer=(
                f"{location_id} has {len(rows)} exception"
                f"{'s' if len(rows) != 1 else ''}{reason_text} "
                f"across {len(record_ids)} record"
                f"{'s' if len(record_ids) != 1 else ''}: "
                f"{join_record_ids(record_ids)}."
            ),
            citations=[row.id for row in rows],
            supported=True,
        )

    if reason_code:
        rows = list(
            queryset.filter(reason_code=reason_code)
            .order_by("record_id", "id")
        )

        reason_label = ReasonCode(reason_code).label

        if not rows:
            return GroundedAnswer(
                answer=(
                    f"No visible exceptions were found for: "
                    f"{reason_label}."
                ),
                citations=[],
                supported=True,
            )

        record_ids = sorted(
            {row.record_id for row in rows}
        )

        return GroundedAnswer(
            answer=(
                f"{len(rows)} exception"
                f"{'s' if len(rows) != 1 else ''} were found for "
                f"{reason_label}: "
                f"{join_record_ids(record_ids)}."
            ),
            citations=[row.id for row in rows],
            supported=True,
        )

    if any(
        phrase in normalized_question
        for phrase in (
            "how many exceptions",
            "total exceptions",
            "exception count",
            "number of exceptions",
        )
    ):
        rows = list(queryset.order_by("id"))

        return GroundedAnswer(
            answer=(
                f"There are {len(rows)} visible reconciliation "
                f"exception{'s' if len(rows) != 1 else ''}."
            ),
            citations=[row.id for row in rows],
            supported=True,
        )

    if any(
        phrase in normalized_question
        for phrase in (
            "list exceptions",
            "show exceptions",
            "which records have exceptions",
            "records with exceptions",
        )
    ):
        rows = list(
            queryset.order_by("record_id", "id")
        )

        if not rows:
            return GroundedAnswer(
                answer="No visible reconciliation exceptions were found.",
                citations=[],
                supported=True,
            )

        record_ids = sorted(
            {row.record_id for row in rows}
        )

        return GroundedAnswer(
            answer=(
                f"Visible exceptions exist for "
                f"{len(record_ids)} record"
                f"{'s' if len(record_ids) != 1 else ''}: "
                f"{join_record_ids(record_ids)}."
            ),
            citations=[row.id for row in rows],
            supported=True,
        )

    return GroundedAnswer(
        answer=(
            "I cannot answer that from the visible reconciliation "
            "exception rows. Ask about exception counts, record IDs, "
            "location IDs, missing records, duplicates, or mismatch types."
        ),
        citations=[],
        supported=False,
    )
