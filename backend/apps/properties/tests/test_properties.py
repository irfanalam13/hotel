from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.common.context import use_tenant
from apps.common.exceptions import ValidationError
from apps.organizations import services as org_services
from apps.properties import services
from apps.properties.models import Property

User = get_user_model()


def auth(client, email, password="pw-strong-123"):
    user = User.objects.create_user(email=email, password=password)
    resp = client.post(reverse("token_obtain_pair"), {"email": email, "password": password}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return user


class PropertyTenantIsolationTests(APITestCase):
    def test_manager_scopes_by_active_tenant(self):
        u1 = User.objects.create_user(email="a@x.test", password="pw-strong-123")
        u2 = User.objects.create_user(email="b@y.test", password="pw-strong-123")
        org1 = org_services.create_organization(name="Org One", owner=u1)
        org2 = org_services.create_organization(name="Org Two", owner=u2)
        services.create_property(organization=org1, name="Alpha Hotel")
        services.create_property(organization=org2, name="Beta Hotel")

        with use_tenant(org1):
            names = list(Property.objects.values_list("name", flat=True))
        self.assertEqual(names, ["Alpha Hotel"])

    def test_quota_enforced(self):
        owner = User.objects.create_user(email="c@z.test", password="pw-strong-123")
        org = org_services.create_organization(name="Tiny", owner=owner)  # FREE => max 1
        services.create_property(organization=org, name="Only One")
        with self.assertRaises(ValidationError):
            services.create_property(organization=org, name="Second")


class PropertyAPITests(APITestCase):
    def test_crud_flow(self):
        auth(self.client, "owner@hotel.test")
        slug = self.client.post(
            reverse("organizations:organization-list"),
            {"name": "Hotel Group", "plan": "PRO"},
            format="json",
        ).data["slug"]
        # PRO plan still defaults max_properties=1; bump it for the test.
        from apps.organizations.models import Organization
        Organization.objects.filter(slug=slug).update(max_properties=10)

        headers = {"HTTP_X_ORG_SLUG": slug}
        create = self.client.post(
            reverse("properties:property-list"), {"name": "Sunrise Resort", "city": "Pokhara"},
            format="json", **headers,
        )
        self.assertEqual(create.status_code, 201, create.data)
        prop_id = create.data["id"]

        listing = self.client.get(reverse("properties:property-list"), **headers)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["count"], 1)

        detail_url = reverse("properties:property-detail", args=[prop_id])
        patch = self.client.patch(detail_url, {"city": "Kathmandu"}, format="json", **headers)
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.data["city"], "Kathmandu")

        delete = self.client.delete(detail_url, **headers)
        self.assertEqual(delete.status_code, 204)
        self.assertEqual(self.client.get(reverse("properties:property-list"), **headers).data["count"], 0)

    def test_requires_tenant_header(self):
        auth(self.client, "noheader@hotel.test")
        # No X-Org-Slug -> no membership -> forbidden.
        resp = self.client.get(reverse("properties:property-list"))
        self.assertEqual(resp.status_code, 403)
