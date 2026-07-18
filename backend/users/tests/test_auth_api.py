from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from tenants.models import Organization
from users.models import UserProfile


User = get_user_model()


class AuthenticationAPITest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            org_id="ORG-TEST",
            name="Test Organization",
        )

        self.user = User.objects.create_user(
            username="USER-A",
            password="test-password",
        )

        UserProfile.objects.create(
            user=self.user,
            organization=self.organization,
        )

    def test_login_username_is_case_insensitive(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "user-a",
                "password": "test-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["user"]["username"],
            "USER-A",
        )

    def test_login_rejects_invalid_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "user-a",
                "password": "wrong-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
