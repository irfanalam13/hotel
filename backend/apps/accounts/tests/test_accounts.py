from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts import services
from apps.common.exceptions import ConflictError

User = get_user_model()


class UserModelTests(APITestCase):
    def test_create_user_lowercases_domain_and_hashes_password(self):
        user = services.create_user(email="Owner@Example.com", password="s3cret-pass-1")
        self.assertTrue(user.check_password("s3cret-pass-1"))
        self.assertFalse(user.is_staff)
        self.assertEqual(str(user), "Owner@example.com")

    def test_duplicate_email_rejected(self):
        services.create_user(email="dup@example.com", password="s3cret-pass-1")
        with self.assertRaises(ConflictError):
            services.create_user(email="dup@example.com", password="s3cret-pass-2")

    def test_superuser_flags(self):
        admin = User.objects.create_superuser(email="root@example.com", password="x")
        self.assertTrue(admin.is_staff and admin.is_superuser)


class AccountsAPITests(APITestCase):
    def test_register_then_login_and_fetch_me(self):
        resp = self.client.post(
            reverse("accounts:register"),
            {"email": "jane@example.com", "password": "Str0ng-pass-99", "full_name": "Jane"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

        token = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "jane@example.com", "password": "Str0ng-pass-99"},
            format="json",
        )
        self.assertEqual(token.status_code, 200, token.data)
        access = token.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me = self.client.get(reverse("accounts:me"))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["email"], "jane@example.com")

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 401)
