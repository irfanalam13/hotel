from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.common.exceptions import ValidationError
from apps.organizations import services
from apps.organizations.models import Membership, Organization
from apps.rbac.constants import Role

User = get_user_model()


def auth(client, email, password="pw-strong-123"):
    user = User.objects.create_user(email=email, password=password)
    resp = client.post(reverse("token_obtain_pair"), {"email": email, "password": password}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return user


class OrganizationServiceTests(APITestCase):
    def test_create_org_provisions_roles_and_owner(self):
        owner = User.objects.create_user(email="o@acme.test", password="pw-strong-123")
        org = services.create_organization(name="Acme", owner=owner)
        self.assertTrue(Organization.objects.filter(slug="acme").exists())
        membership = Membership.objects.get(organization=org, user=owner)
        self.assertEqual(membership.role.code, Role.OWNER)

    def test_cannot_remove_last_owner(self):
        owner = User.objects.create_user(email="o2@acme.test", password="pw-strong-123")
        org = services.create_organization(name="Acme Two", owner=owner)
        membership = Membership.objects.get(organization=org, user=owner)
        with self.assertRaises(ValidationError):
            services.remove_member(membership=membership)


class OrganizationAPITests(APITestCase):
    def test_create_and_list_my_orgs(self):
        auth(self.client, "founder@acme.test")
        resp = self.client.post(reverse("organizations:organization-list"), {"name": "Grand Hotel"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        slug = resp.data["slug"]

        listing = self.client.get(reverse("organizations:organization-list"))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data["results"]), 1)

        # Member management requires the tenant header.
        members = self.client.get(reverse("organizations:member-list"), HTTP_X_ORG_SLUG=slug)
        self.assertEqual(members.status_code, 200)
        self.assertEqual(len(members.data), 1)

    def test_invite_member(self):
        auth(self.client, "boss@acme.test")
        slug = self.client.post(
            reverse("organizations:organization-list"), {"name": "Palace"}, format="json"
        ).data["slug"]
        resp = self.client.post(
            reverse("organizations:member-invite"),
            {"email": "clerk@acme.test", "role_code": Role.RECEPTIONIST},
            format="json",
            HTTP_X_ORG_SLUG=slug,
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["role_code"], Role.RECEPTIONIST)

    def test_non_member_cannot_view_members(self):
        owner = User.objects.create_user(email="owner3@acme.test", password="pw-strong-123")
        org = services.create_organization(name="Closed Inn", owner=owner)
        auth(self.client, "outsider@acme.test")
        resp = self.client.get(reverse("organizations:member-list"), HTTP_X_ORG_SLUG=org.slug)
        self.assertEqual(resp.status_code, 403)
