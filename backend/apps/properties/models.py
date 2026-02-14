import uuid
from django.db import models

class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=50, unique=True)  # e.g. "hotel-abc"
    timezone = models.CharField(max_length=64, default="Asia/Kathmandu")
    currency = models.CharField(max_length=10, default="NPR")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Amenity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="amenities")
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = [("property", "name")]

    def __str__(self):
        return self.name

class RoomType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="room_types")
    name = models.CharField(max_length=120)  # Deluxe, Standard
    code = models.SlugField(max_length=40)   # deluxe, standard
    max_adults = models.PositiveSmallIntegerField(default=2)
    max_children = models.PositiveSmallIntegerField(default=0)
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # fallback price

    amenities = models.ManyToManyField(Amenity, blank=True, related_name="room_types")

    class Meta:
        unique_together = [("property", "code")]

    def __str__(self):
        return f"{self.name} ({self.property.code})"

class Room(models.Model):
    class HousekeepingStatus(models.TextChoices):
        CLEAN = "clean", "Clean"
        DIRTY = "dirty", "Dirty"
        INSPECT = "inspect", "Needs Inspection"
        OOO = "ooo", "Out of Order"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="rooms")
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="rooms")
    number = models.CharField(max_length=20)  # "101", "A-12"
    floor = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)

    housekeeping_status = models.CharField(
        max_length=20, choices=HousekeepingStatus.choices, default=HousekeepingStatus.CLEAN
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("property", "number")]
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.room_type.name}"
