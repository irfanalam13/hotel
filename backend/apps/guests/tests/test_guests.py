from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.common.context import use_tenant
from apps.guests import services
from apps.guests.models import Guest
from apps.organizations.services import create_organization
from apps.properties.services import create_property

User = get_user_model()


class GuestServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@guests.test", password="pw-strong-123")
        self.org = create_organization(name="Guests Co", owner=self.owner)
        self.prop = create_property(organization=self.org, name="Hotel A")

    def test_create_and_full_name(self):
        guest = services.create_guest(
            organization=self.org, property=self.prop, first_name="Ada", last_name="Lovelace"
        )
        self.assertEqual(guest.full_name, "Ada Lovelace")

    def test_tenant_isolation(self):
        other_owner = User.objects.create_user(email="o2@guests.test", password="pw-strong-123")
        other_org = create_organization(name="Other Co", owner=other_owner)
        other_prop = create_property(organization=other_org, name="Hotel B")
        services.create_guest(organization=self.org, property=self.prop, first_name="A")
        services.create_guest(organization=other_org, property=other_prop, first_name="B")

        with use_tenant(self.org):
            self.assertEqual(Guest.objects.count(), 1)
            self.assertEqual(Guest.objects.first().first_name, "A")
