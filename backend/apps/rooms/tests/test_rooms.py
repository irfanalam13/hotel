from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.common.exceptions import ConflictError, ValidationError
from apps.organizations.services import create_organization
from apps.properties.services import create_property
from apps.rooms import services
from apps.rooms.models import Room, RoomType

User = get_user_model()


class RoomsServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@rooms.test", password="pw-strong-123")
        self.org = create_organization(name="Rooms Co", owner=self.owner)
        self.org.max_properties = 5
        self.org.save(update_fields=["max_properties"])
        self.prop = create_property(organization=self.org, name="Main Hotel")

    def test_create_room_type_and_room(self):
        rt = services.create_room_type(
            organization=self.org, property=self.prop, name="Deluxe", base_rate=120, max_adults=3
        )
        self.assertEqual(rt.code, "deluxe")
        room = services.create_room(
            organization=self.org, property=self.prop, room_type=rt, number="101"
        )
        self.assertEqual(room.status, Room.Status.VACANT_CLEAN)
        self.assertTrue(room.is_bookable)

    def test_duplicate_room_number_rejected(self):
        rt = services.create_room_type(organization=self.org, property=self.prop, name="Std")
        services.create_room(organization=self.org, property=self.prop, room_type=rt, number="201")
        with self.assertRaises(ConflictError):
            services.create_room(organization=self.org, property=self.prop, room_type=rt, number="201")

    def test_room_type_must_match_property(self):
        other = create_property(organization=self.org, name="Annex")
        rt = services.create_room_type(organization=self.org, property=other, name="Suite")
        with self.assertRaises(ValidationError):
            services.create_room(organization=self.org, property=self.prop, room_type=rt, number="301")

    def test_set_room_status(self):
        rt = services.create_room_type(organization=self.org, property=self.prop, name="Eco")
        room = services.create_room(organization=self.org, property=self.prop, room_type=rt, number="401")
        services.set_room_status(room=room, status=Room.Status.OUT_OF_ORDER)
        room.refresh_from_db()
        self.assertFalse(room.is_bookable)
