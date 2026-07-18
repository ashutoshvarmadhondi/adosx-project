from django.db import connection
from django.test import TransactionTestCase

from reconciliation.models import ReconciliationException, ReasonCode
from tenants.db_context import tenant_database_context
from tenants.models import Location, Organization


class ReconciliationExceptionRLSTest(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def setUp(self):
        super().setUpClass()

        # The test runner creates the database as the Django application role.
        # The RLS migration must already be applied to the test database.
        self.org_a = Organization.objects.create(
            org_id="ORG-A",
            name="Organization A",
        )
        self.org_b = Organization.objects.create(
            org_id="ORG-B",
            name="Organization B",
        )

        self.location_a = Location.objects.create(
            location_id="LOC-101",
            name="Location 101",
            organization=self.org_a,
        )
        self.location_b = Location.objects.create(
            location_id="LOC-201",
            name="Location 201",
            organization=self.org_b,
        )

        with tenant_database_context(self.org_a):
            self.exception_a = ReconciliationException.objects.create(
                organization=self.org_a,
                location=self.location_a,
                record_id="REC-A",
                reason_code=ReasonCode.VALUE_MISMATCH,
                reason="System A and System B recorded different values",
            )

        with tenant_database_context(self.org_b):
            self.exception_b = ReconciliationException.objects.create(
                organization=self.org_b,
                location=self.location_b,
                record_id="REC-B",
                reason_code=ReasonCode.DATE_MISMATCH,
                reason="System A and System B recorded different dates",
            )

    def test_unfiltered_orm_query_only_returns_current_org_rows(self):
        with tenant_database_context(self.org_a):
            rows = list(
                ReconciliationException.objects.all().values_list(
                    "record_id",
                    flat=True,
                )
            )

        self.assertEqual(rows, ["REC-A"])
        self.assertNotIn("REC-B", rows)

    def test_raw_sql_cannot_return_other_org_rows(self):
        with tenant_database_context(self.org_a):
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT record_id
                    FROM reconciliation_reconciliationexception
                    ORDER BY record_id
                    """
                )
                rows = [row[0] for row in cursor.fetchall()]

        self.assertEqual(rows, ["REC-A"])
        self.assertNotIn("REC-B", rows)

    def test_insert_for_another_org_is_rejected(self):
        with self.assertRaises(Exception):
            with tenant_database_context(self.org_a):
                ReconciliationException.objects.create(
                    organization=self.org_b,
                    location=self.location_b,
                    record_id="REC-CROSS-TENANT",
                    reason_code=ReasonCode.VALUE_MISMATCH,
                    reason="Cross-tenant insert must be rejected",
                )
