from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.common.exceptions import ConflictError, ValidationError
from apps.guests.services import create_guest
from apps.organizations.services import create_organization
from apps.properties.services import create_property
from apps.reservations import selectors, services
from apps.reservations.models import ReservationStatus
from apps.rooms.models import Room
from apps.rooms.services import create_room, create_room_type

User = get_user_model()

D1 = date(2030, 1, 10)
D2 = date(2030, 1, 12)
D3 = date(2030, 1, 14)


class ReservationEngineTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@resv.test", password="pw-strong-123")
        self.org = create_organization(name="Resv Co", owner=self.owner)
        self.prop = create_property(organization=self.org, name="Grand")
        self.rt = create_room_type(
            organization=self.org, property=self.prop, name="Standard", base_rate=100
        )
        self.room = create_room(
            organization=self.org, property=self.prop, room_type=self.rt, number="101"
        )

    def _book(self, check_in=D1, check_out=D3, room_id=None):
        req = {"room_type_id": self.rt.id, "adults": 1}
        if room_id:
            req["room_id"] = room_id
        return services.create_reservation(
            organization=self.org, property=self.prop,
            check_in=check_in, check_out=check_out, room_requests=[req], by_user=self.owner,
        )

    def test_availability_summary(self):
        summary = selectors.availability_summary(
            organization=self.org, property=self.prop, check_in=D1, check_out=D3
        )
        self.assertEqual(summary[0]["available"], 1)
        self.assertEqual(summary[0]["nights"], 4)
        self.assertEqual(summary[0]["total_price"], 400)

    def test_create_assigns_room_and_computes_total(self):
        r = self._book()
        self.assertEqual(r.status, ReservationStatus.BOOKED)
        self.assertEqual(r.code, "RSV-000001")
        line = r.rooms.get()
        self.assertEqual(line.room_id, self.room.id)
        self.assertEqual(line.nights, 4)
        self.assertEqual(r.total_amount, 400)

    def test_double_booking_prevented_same_type(self):
        self._book(D1, D3)
        # Only one room of this type; an overlapping range has no availability.
        with self.assertRaises(ConflictError):
            self._book(D2, date(2030, 1, 16))

    def test_double_booking_prevented_same_room(self):
        self._book(D1, D3)
        with self.assertRaises(ConflictError):
            self._book(D2, date(2030, 1, 16), room_id=self.room.id)

    def test_adjacent_dates_allowed(self):
        self._book(D1, D2)
        r2 = self._book(D2, D3)  # checkout day is free -> no overlap
        self.assertEqual(r2.status, ReservationStatus.BOOKED)

    def test_cancel_frees_inventory(self):
        r = self._book(D1, D3)
        services.cancel_reservation(reservation=r, by_user=self.owner)
        # Now the same dates are bookable again.
        r2 = self._book(D1, D3)
        self.assertEqual(r2.status, ReservationStatus.BOOKED)

    def test_out_of_order_room_excluded(self):
        self.room.status = Room.Status.OUT_OF_ORDER
        self.room.save(update_fields=["status"])
        with self.assertRaises(ConflictError):
            self._book()

    def test_check_in_and_out_updates_room_status(self):
        r = self._book(D1, D3)
        services.check_in(reservation=r, by_user=self.owner)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, Room.Status.OCCUPIED)
        self.assertEqual(r.status, ReservationStatus.CHECKED_IN)

        services.check_out(reservation=r, by_user=self.owner)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, Room.Status.VACANT_DIRTY)

    def test_cannot_check_out_without_check_in(self):
        r = self._book(D1, D3)
        with self.assertRaises(ValidationError):
            services.check_out(reservation=r, by_user=self.owner)

    def test_modify_dates_revalidates_and_recomputes(self):
        r = self._book(D1, D2)  # 2 nights, 200
        services.modify_reservation(reservation=r, check_out=D3, by_user=self.owner)
        r.refresh_from_db()
        self.assertEqual(r.check_out, D3)
        self.assertEqual(r.total_amount, 400)  # 4 nights * 100

    def test_status_log_recorded(self):
        r = self._book(D1, D3)
        services.check_in(reservation=r, by_user=self.owner)
        services.check_out(reservation=r, by_user=self.owner)
        statuses = list(r.status_logs.values_list("to_status", flat=True))
        self.assertIn(ReservationStatus.CHECKED_IN, statuses)
        self.assertIn(ReservationStatus.CHECKED_OUT, statuses)


class ReservationAPITests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.owner = User.objects.create_user(email="api@resv.test", password="pw-strong-123")
        self.org = create_organization(name="API Hotels", owner=self.owner)
        self.prop = create_property(organization=self.org, name="API Hotel")
        self.rt = create_room_type(organization=self.org, property=self.prop, name="Std", base_rate=80)
        self.room = create_room(organization=self.org, property=self.prop, room_type=self.rt, number="1")
        self.guest = create_guest(organization=self.org, property=self.prop, first_name="Sam")

        token = self.client.post(
            "/api/auth/token/", {"email": "api@resv.test", "password": "pw-strong-123"}, format="json"
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_ORG_SLUG=self.org.slug)

    def test_availability_then_book_then_check_in(self):
        avail = self.client.get(
            "/api/reservations/availability/",
            {"property": str(self.prop.id), "check_in": "2030-02-01", "check_out": "2030-02-03"},
        )
        self.assertEqual(avail.status_code, 200, avail.data)
        self.assertEqual(avail.data[0]["available"], 1)

        create = self.client.post(
            "/api/reservations/",
            {
                "property": str(self.prop.id),
                "check_in": "2030-02-01",
                "check_out": "2030-02-03",
                "primary_guest": str(self.guest.id),
                "rooms": [{"room_type_id": str(self.rt.id), "adults": 2}],
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201, create.data)
        rid = create.data["id"]
        self.assertEqual(create.data["total_amount"], "160.00")

        checkin = self.client.post(f"/api/reservations/{rid}/check-in/")
        self.assertEqual(checkin.status_code, 200, checkin.data)
        self.assertEqual(checkin.data["status"], "checked_in")

    def test_double_booking_returns_409(self):
        payload = {
            "property": str(self.prop.id),
            "check_in": "2030-03-01",
            "check_out": "2030-03-05",
            "rooms": [{"room_type_id": str(self.rt.id)}],
        }
        first = self.client.post("/api/reservations/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        second = self.client.post("/api/reservations/", payload, format="json")
        self.assertEqual(second.status_code, 409, second.data)

    def test_housekeeping_cannot_create_reservation(self):
        from apps.organizations.services import add_member

        hk = User.objects.create_user(email="hk@resv.test", password="pw-strong-123")
        add_member(organization=self.org, user=hk, role_code="HOUSEKEEPING")
        token = self.client.post(
            "/api/auth/token/", {"email": "hk@resv.test", "password": "pw-strong-123"}, format="json"
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_ORG_SLUG=self.org.slug)
        resp = self.client.post(
            "/api/reservations/",
            {"property": str(self.prop.id), "check_in": "2030-04-01", "check_out": "2030-04-02",
             "rooms": [{"room_type_id": str(self.rt.id)}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.data)
