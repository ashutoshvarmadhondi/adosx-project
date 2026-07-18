from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from reconciliation.models import ReconciliationException
from reconciliation.services import (
    group_system_b_entries,
    load_system_a_csv,
    load_system_b_csv,
    reconcile_records,
)
from tenants.db_context import tenant_database_context
from tenants.models import Location


class Command(BaseCommand):
    help = "Reconcile System A and System B CSV files and save exceptions."

    def add_arguments(self, parser):
        parser.add_argument("system_a_csv", type=str)
        parser.add_argument("system_b_csv", type=str)

    def handle(self, *args, **options):
        system_a_path = Path(options["system_a_csv"])
        system_b_path = Path(options["system_b_csv"])

        if not system_a_path.exists():
            raise CommandError(
                f"System A file not found: {system_a_path}"
            )

        if not system_b_path.exists():
            raise CommandError(
                f"System B file not found: {system_b_path}"
            )

        system_a_records = load_system_a_csv(system_a_path)
        system_b_entries = load_system_b_csv(system_b_path)

        findings = reconcile_records(
            system_a_records,
            system_b_entries,
        )

        system_a_by_id = {
            record.record_id: record
            for record in system_a_records
            if record.record_id
        }

        grouped_system_b, _ = group_system_b_entries(
            system_b_entries
        )

        locations = {
            location.location_id: location
            for location in Location.objects.select_related(
                "organization"
            )
        }

        resolved_findings = []
        skipped_findings = []

        for finding in findings:
            system_a_record = system_a_by_id.get(
                finding.record_id
            )
            system_b_group = grouped_system_b.get(
                finding.record_id,
                [],
            )

            location = None

            # Prefer System A location because the exception belongs to
            # the organization whose source record is being reconciled.
            if system_a_record:
                location = locations.get(
                    system_a_record.location_id
                )

            # Records missing from System A must derive their tenant
            # from the System B location.
            if location is None:
                system_b_locations = {
                    locations[entry.location_id]
                    for entry in system_b_group
                    if entry.location_id in locations
                }

                system_b_organizations = {
                    item.organization_id
                    for item in system_b_locations
                }

                if len(system_b_organizations) == 1:
                    location = sorted(
                        system_b_locations,
                        key=lambda item: item.location_id,
                    )[0]

            if location is None:
                skipped_findings.append(finding)
                continue

            resolved_findings.append(
                (
                    finding,
                    location.organization,
                    location,
                )
            )

        organizations = {
            organization.pk: organization
            for _, organization, _ in resolved_findings
        }

        # Make rerunning the command deterministic.
        for organization in organizations.values():
            with tenant_database_context(organization):
                ReconciliationException.objects.all().delete()

        created_count = 0

        for finding, organization, location in resolved_findings:
            with tenant_database_context(organization):
                ReconciliationException.objects.create(
                    organization=organization,
                    location=location,
                    record_id=finding.record_id,
                    reason_code=finding.reason_code,
                    reason=finding.reason,
                    system_a_record_id=(
                        finding.system_a_record_id
                    ),
                    system_b_entry_ids=(
                        finding.system_b_entry_ids
                    ),
                    evidence=finding.evidence,
                )

            created_count += 1

        reason_counts = Counter(
            finding.reason_code
            for finding, _, _ in resolved_findings
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciliation completed: "
                f"{created_count} exceptions saved."
            )
        )

        for reason_code, count in sorted(
            reason_counts.items()
        ):
            self.stdout.write(
                f"{reason_code}: {count}"
            )

        if skipped_findings:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(skipped_findings)} findings were not "
                    "saved because their organization could not "
                    "be determined."
                )
            )

            for finding in skipped_findings:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped {finding.record_id}: "
                        f"{finding.reason_code}"
                    )
                )
