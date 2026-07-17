import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tenants.models import Location, Organization


class Command(BaseCommand):
    help = "Import organizations and locations from locations.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Path to locations.csv",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])

        if not csv_path.exists():
            raise CommandError(f"File not found: {csv_path}")

        required_columns = {
            "location_id",
            "org_id",
            "location_name",
        }

        created_orgs = 0
        created_locations = 0
        updated_locations = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            if not reader.fieldnames:
                raise CommandError("CSV file has no header row.")

            missing_columns = required_columns - set(reader.fieldnames)

            if missing_columns:
                raise CommandError(
                    f"Missing required columns: {', '.join(sorted(missing_columns))}"
                )

            for row_number, row in enumerate(reader, start=2):
                location_id = row["location_id"].strip()
                org_id = row["org_id"].strip()
                location_name = row["location_name"].strip()

                if not location_id or not org_id or not location_name:
                    raise CommandError(
                        f"Row {row_number} contains an empty required value."
                    )

                organization, org_created = Organization.objects.get_or_create(
                    org_id=org_id,
                    defaults={"name": org_id},
                )

                if org_created:
                    created_orgs += 1

                location, location_created = Location.objects.update_or_create(
                    location_id=location_id,
                    defaults={
                        "name": location_name,
                        "organization": organization,
                    },
                )

                if location_created:
                    created_locations += 1
                else:
                    updated_locations += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Import completed: "
                f"{created_orgs} organizations created, "
                f"{created_locations} locations created, "
                f"{updated_locations} locations updated."
            )
        )
