from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from reconciliation.models import ReconciliationException, ReasonCode
from tenants.db_context import tenant_database_context
from tenants.models import Location, Organization
from users.models import UserProfile


User = get_user_model()


class ReconciliationExceptionAPITest(APITestCase):
    def setUp(self):
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
            organization=self.org_a,
            name="Location 101",
        )
        self.location_b = Location.objects.create(
            location_id="LOC-201",
            organization=self.org_b,
            name="Location 201",
        )

        self.user_a = User.objects.create_user(
            username="USER-A",
            password="test-password",
        )
        self.user_b = User.objects.create_user(
            username="USER-B",
            password="test-password",
        )

        UserProfile.objects.create(
            user=self.user_a,
            organization=self.org_a,
        )
        UserProfile.objects.create(
            user=self.user_b,
            organization=self.org_b,
        )

        with tenant_database_context(self.org_a):
            ReconciliationException.objects.create(
                organization=self.org_a,
                location=self.location_a,
                record_id="REC-1001",
                reason_code=ReasonCode.VALUE_MISMATCH,
                reason=ReasonCode.VALUE_MISMATCH.label,
                system_a_record_id="REC-1001",
                system_b_entry_ids=["ENT-A"],
                evidence={},
            )

        with tenant_database_context(self.org_b):
            ReconciliationException.objects.create(
                organization=self.org_b,
                location=self.location_b,
                record_id="REC-2001",
                reason_code=ReasonCode.DATE_MISMATCH,
                reason=ReasonCode.DATE_MISMATCH.label,
                system_a_record_id="REC-2001",
                system_b_entry_ids=["ENT-B"],
                evidence={},
            )

    def test_requires_authentication(self):
        response = self.client.get("/api/exceptions/")

        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", response.data)

    def test_returns_only_authenticated_users_organization(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get("/api/exceptions/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["record_id"],
            "REC-1001",
        )
        self.assertEqual(
            response.data["results"][0]["organization_id"],
            "ORG-A",
        )

    def test_filters_by_reason_code(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            "/api/exceptions/",
            {"reason_code": ReasonCode.VALUE_MISMATCH},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_returns_empty_result_for_nonmatching_filter(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            "/api/exceptions/",
            {"location_id": "LOC-201"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_rejects_invalid_reason_code(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            "/api/exceptions/",
            {"reason_code": "NOT_A_REASON"},
        )

        self.assertEqual(response.status_code, 400)
