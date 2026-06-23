from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.audit.models import AuditLog
from apps.audit.services import redact
from apps.organizations import services as org_services

User = get_user_model()


def auth(client, email, password="pw-strong-123"):
    user = User.objects.create_user(email=email, password=password)
    resp = client.post(reverse("token_obtain_pair"), {"email": email, "password": password}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return user


class RedactionTests(APITestCase):
    def test_sensitive_keys_masked(self):
        out = redact({"email": "a@b.c", "password": "hunter2", "nested": {"token": "abc"}})
        self.assertEqual(out["email"], "a@b.c")
        self.assertEqual(out["password"], "***")
        self.assertEqual(out["nested"]["token"], "***")


class AuditMiddlewareTests(APITestCase):
    def test_mutation_creates_redacted_audit_row(self):
        self.client.post(
            reverse("accounts:register"),
            {"email": "newbie@x.test", "password": "Str0ng-pass-99"},
            format="json",
        )
        log = AuditLog.objects.filter(path="/api/accounts/auth/register/").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.method, "POST")
        self.assertEqual(log.changes["body"]["password"], "***")


class AuditAPITests(APITestCase):
    def test_owner_can_read_audit_log(self):
        owner = auth(self.client, "owner@audit.test")
        org = org_services.create_organization(name="Audited Co", owner=owner)
        resp = self.client.get(reverse("audit:auditlog-list"), HTTP_X_ORG_SLUG=org.slug)
        self.assertEqual(resp.status_code, 200, resp.data)

    def test_front_desk_cannot_read_audit_log(self):
        owner = User.objects.create_user(email="o@audit2.test", password="pw-strong-123")
        org = org_services.create_organization(name="Audited Two", owner=owner)
        clerk = auth(self.client, "clerk@audit2.test")
        org_services.add_member(organization=org, user=clerk, role_code="RECEPTIONIST")
        resp = self.client.get(reverse("audit:auditlog-list"), HTTP_X_ORG_SLUG=org.slug)
        self.assertEqual(resp.status_code, 403)
