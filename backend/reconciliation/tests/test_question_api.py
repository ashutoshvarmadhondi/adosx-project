from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from reconciliation.models import ReconciliationException, ReasonCode
from tenants.db_context import tenant_database_context
from tenants.models import Location, Organization
from users.models import UserProfile


User = get_user_model()


class ReconciliationExceptionQuestionAPITest(APITestCase):
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
            self.org_a_exception = (
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
            )

        with tenant_database_context(self.org_b):
            self.org_b_exception = (
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
            )

    def test_requires_authentication(self):
        response = self.client.post(
            "/api/exceptions/ask/",
            {"question": "How many exceptions are there?"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_answers_from_visible_rows_only(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            "/api/exceptions/ask/",
            {"question": "How many exceptions are there?"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["supported"])
        self.assertEqual(
            response.data["citations"],
            [self.org_a_exception.id],
        )
        self.assertNotIn(
            self.org_b_exception.id,
            response.data["citations"],
        )

    def test_answers_reason_code_question(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            "/api/exceptions/ask/",
            {
                "question": (
                    "Which records have value mismatches?"
                )
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["supported"])
        self.assertIn(
            "REC-1001",
            response.data["answer"],
        )
        self.assertEqual(
            response.data["citations"],
            [self.org_a_exception.id],
        )

    def test_answers_record_question(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            "/api/exceptions/ask/",
            {
                "question": (
                    "What happened with REC-1001?"
                )
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["supported"])
        self.assertIn(
            "REC-1001",
            response.data["answer"],
        )

    def test_refuses_unsupported_question(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            "/api/exceptions/ask/",
            {
                "question": (
                    "What will revenue be next year?"
                )
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["supported"])
        self.assertEqual(response.data["citations"], [])

    def test_does_not_expose_other_tenant_record(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            "/api/exceptions/ask/",
            {
                "question": (
                    "What happened with REC-2001?"
                )
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["supported"])
        self.assertEqual(response.data["citations"], [])
        self.assertNotIn(
            "date mismatch",
            response.data["answer"].casefold(),
        )
