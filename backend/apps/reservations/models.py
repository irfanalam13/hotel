import uuid
from datetime import date
from django.db import models
from django.core.exceptions import ValidationError

from apps.properties.models import Property, RoomType, Room
from apps.guests.models import Guest

class Reservation(models.Model):
    class Status(models.TextChoices):
        INQUIRY = "inquiry", "Inquiry"
        BOOKED = "booked", "Booked"
        CHECKED_IN = "checked_in", "Checked-in"
        CHECKED_OUT = "checked_out", "Checked-out"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No-show"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reservations")

    code = models.CharField(max_length=20, db_index=True)  # e.g. RSV-000123 (set in save)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INQUIRY)

    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="reservations")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, null=True, blank=True, related_name="reservations")

    check_in = models.DateField()
    check_out = models.DateField()

    adults = models.PositiveSmallIntegerField(default=2)
    children = models.PositiveSmallIntegerField(default=0)

    source = models.CharField(max_length=80, blank=True, default="front_desk")  # walk-in, booking.com, etc.
    special_requests = models.TextField(blank=True, default="")
    internal_notes = models.TextField(blank=True, default="")

    guests = models.ManyToManyField(Guest, through="ReservationGuest", related_name="reservations")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["property", "status"]),
            models.Index(fields=["property", "check_in", "check_out"]),
            models.Index(fields=["property", "code"]),
        ]

    def clean(self):
        if self.check_in >= self.check_out:
            raise ValidationError("check_out must be after check_in.")
        if self.adults > self.room_type.max_adults:
            raise ValidationError("Adults exceed room type capacity.")
        if self.children > self.room_type.max_children:
            raise ValidationError("Children exceed room type capacity.")
        if self.room and self.room.property_id != self.property_id:
            raise ValidationError("Room must belong to same property.")
        if self.room and self.room.room_type_id != self.room_type_id:
            raise ValidationError("Room must match reservation room_type.")

    @staticmethod
    def overlaps(a_start, a_end, b_start, b_end):
        # date ranges are [start, end) like hotels: checkout day is free
        return a_start < b_end and b_start < a_end

    def __str__(self):
        return f"{self.code} ({self.status})"

class ReservationGuest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = [("reservation", "guest")]

class RoomMoveLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="moves")
    from_room = models.ForeignKey(Room, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    to_room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="+")
    moved_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=200, blank=True, default="")

class ReservationCharge(models.Model):
    """
    Real-life: keep basic folio lines (room charges, minibar, extra bed, etc.)
    """
    class Kind(models.TextChoices):
        ROOM = "room", "Room"
        EXTRA = "extra", "Extra"
        TAX = "tax", "Tax"
        DISCOUNT = "discount", "Discount"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="charges")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    posted_on = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
