"""
Reservations domain.

A ``Reservation`` is the booking header for a stay ``[check_in, check_out)``
(half-open: the checkout day is free). Each booked room is a ``ReservationRoom``
line referencing a concrete ``Room`` once assigned — this room-level assignment
is what makes double-booking prevention rigorous (lock the room rows, re-check
overlap, commit).
"""
from __future__ import annotations

import builtins
from datetime import date

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel, TenantScopedModel


class ReservationStatus(models.TextChoices):
    INQUIRY = "inquiry", "Inquiry"
    BOOKED = "booked", "Booked"
    CHECKED_IN = "checked_in", "Checked-in"
    CHECKED_OUT = "checked_out", "Checked-out"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No-show"


# Statuses that occupy inventory and therefore block other bookings.
BLOCKING_STATUSES = (ReservationStatus.BOOKED, ReservationStatus.CHECKED_IN)


class Reservation(TenantScopedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="reservations"
    )
    code = models.CharField(max_length=24, db_index=True)
    status = models.CharField(
        max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.BOOKED
    )

    primary_guest = models.ForeignKey(
        "guests.Guest", on_delete=models.PROTECT, null=True, blank=True, related_name="reservations"
    )
    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)

    source = models.CharField(max_length=80, blank=True, default="front_desk")
    special_requests = models.TextField(blank=True, default="")
    internal_notes = models.TextField(blank=True, default="")

    currency = models.CharField(max_length=8, blank=True, default="")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "code"], name="uniq_reservation_code"),
            models.CheckConstraint(
                condition=models.Q(check_out__gt=models.F("check_in")),
                name="reservation_checkout_after_checkin",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "property", "status"]),
            models.Index(fields=["property", "check_in", "check_out"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.status})"

    @builtins.property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days

    @staticmethod
    def ranges_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
        """Half-open overlap: True if [a_start, a_end) intersects [b_start, b_end)."""
        return a_start < b_end and b_start < a_end


class ReservationRoom(TenantScopedModel):
    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="rooms"
    )
    room_type = models.ForeignKey(
        "rooms.RoomType", on_delete=models.PROTECT, related_name="reservation_rooms"
    )
    room = models.ForeignKey(
        "rooms.Room", on_delete=models.PROTECT, null=True, blank=True, related_name="reservation_rooms"
    )
    nightly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nights = models.PositiveSmallIntegerField(default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["room", "reservation"])]

    def __str__(self) -> str:
        return f"{self.reservation_id} -> room {self.room_id or 'unassigned'}"


class ReservationGuest(BaseModel):
    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="reservation_guests"
    )
    guest = models.ForeignKey("guests.Guest", on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reservation", "guest"], name="uniq_guest_per_reservation"
            )
        ]


class ReservationStatusLog(BaseModel):
    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="status_logs"
    )
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20)
    by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]


class ReservationCharge(TenantScopedModel):
    class Kind(models.TextChoices):
        ROOM = "room", "Room"
        EXTRA = "extra", "Extra"
        TAX = "tax", "Tax"
        DISCOUNT = "discount", "Discount"

    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="charges"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.EXTRA)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    posted_on = models.DateField(default=date.today)

    class Meta:
        ordering = ["-posted_on", "-created_at"]
