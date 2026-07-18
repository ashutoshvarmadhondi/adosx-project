from django.db import models
from tenants.models import Organization, Location


class ReasonCode(models.TextChoices):
    # Record-level presence
    MISSING_IN_SYSTEM_A = (
        "MISSING_IN_SYSTEM_A",
        "Record exists in System B but not in System A",
    )
    MISSING_IN_SYSTEM_B = (
        "MISSING_IN_SYSTEM_B",
        "Record exists in System A but not in System B",
    )

    # Identifier and join problems
    INVALID_SYSTEM_A_RECORD_ID = (
        "INVALID_SYSTEM_A_RECORD_ID",
        "System A record identifier is missing or invalid",
    )
    MISSING_SYSTEM_B_REFERENCE = (
        "MISSING_SYSTEM_B_REFERENCE",
        "System B entry has no record reference",
    )
    INVALID_SYSTEM_B_REFERENCE = (
        "INVALID_SYSTEM_B_REFERENCE",
        "System B record reference is invalid",
    )
    UNRESOLVED_SYSTEM_B_REFERENCE = (
        "UNRESOLVED_SYSTEM_B_REFERENCE",
        "System B reference cannot be matched to a System A record",
    )

    # Location and tenant problems
    MISSING_SYSTEM_A_LOCATION = (
        "MISSING_SYSTEM_A_LOCATION",
        "System A has no location for this record",
    )
    MISSING_SYSTEM_B_LOCATION = (
        "MISSING_SYSTEM_B_LOCATION",
        "System B has no location for this record",
    )
    UNKNOWN_SYSTEM_A_LOCATION = (
        "UNKNOWN_SYSTEM_A_LOCATION",
        "System A location is not present in the location mapping",
    )
    UNKNOWN_SYSTEM_B_LOCATION = (
        "UNKNOWN_SYSTEM_B_LOCATION",
        "System B location is not present in the location mapping",
    )
    LOCATION_MISMATCH = (
        "LOCATION_MISMATCH",
        "System A and System B recorded different locations",
    )
    TENANT_MISMATCH = (
        "TENANT_MISMATCH",
        "System A and System B records belong to different organizations",
    )

    # Date problems
    MISSING_SYSTEM_A_DATE = (
        "MISSING_SYSTEM_A_DATE",
        "System A has no event date for this record",
    )
    MISSING_SYSTEM_B_DATE = (
        "MISSING_SYSTEM_B_DATE",
        "System B has no recorded date for this record",
    )
    INVALID_SYSTEM_A_DATE = (
        "INVALID_SYSTEM_A_DATE",
        "System A event date could not be parsed",
    )
    INVALID_SYSTEM_B_DATE = (
        "INVALID_SYSTEM_B_DATE",
        "System B recorded date could not be parsed",
    )
    DATE_MISMATCH = (
        "DATE_MISMATCH",
        "System A and System B recorded different dates",
    )

    # Value problems
    MISSING_SYSTEM_A_VALUE = (
        "MISSING_SYSTEM_A_VALUE",
        "System A has no total value for this record",
    )
    MISSING_SYSTEM_B_VALUE = (
        "MISSING_SYSTEM_B_VALUE",
        "System B has no value for this record",
    )
    INVALID_SYSTEM_A_VALUE = (
        "INVALID_SYSTEM_A_VALUE",
        "System A total value could not be parsed",
    )
    INVALID_SYSTEM_B_VALUE = (
        "INVALID_SYSTEM_B_VALUE",
        "System B value could not be parsed",
    )
    VALUE_MISMATCH = (
        "VALUE_MISMATCH",
        "System A and System B recorded different total values",
    )

    # Multiple-entry problems
    DUPLICATE_SYSTEM_B_ENTRY = (
        "DUPLICATE_SYSTEM_B_ENTRY",
        "System B contains duplicate entries for this record",
    )
    AMBIGUOUS_SYSTEM_B_ENTRIES = (
        "AMBIGUOUS_SYSTEM_B_ENTRIES",
        "Multiple System B entries exist and cannot be safely reconciled",
    )


class ReconciliationException(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="exceptions",
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="exceptions",
        null=True,
        blank=True,
    )
    record_id = models.CharField(max_length=30)
    reason_code = models.CharField(
        max_length=50,
        choices=ReasonCode.choices,
    )
    reason = models.CharField(max_length=255)
    system_a_record_id = models.CharField(max_length=30, blank=True)
    system_b_entry_ids = models.JSONField(default=list, blank=True)
    evidence = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("record_id", "reason_code")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "record_id", "reason_code"),
                name="unique_exception_per_org_record_reason",
            )
        ]
        indexes = [
            models.Index(fields=("organization", "reason_code")),
            models.Index(fields=("organization", "location")),
        ]

    def __str__(self) -> str:
        return f"{self.record_id} - {self.reason_code}"
