from django.db import models
from django.utils import timezone


class RoomStatus(models.TextChoices):
    VACANT_CLEAN = "vacant_clean", "Vacant Clean"
    VACANT_DIRTY = "vacant_dirty", "Vacant Dirty"
    OCCUPIED = "occupied", "Occupied"
    OUT_OF_ORDER = "out_of_order", "Out of Order"


class Room(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="rooms")
    number = models.CharField(max_length=20)
    floor = models.CharField(max_length=20, blank=True, default="")
    room_type = models.CharField(max_length=50, blank=True, default="standard")
    status = models.CharField(max_length=32, choices=RoomStatus.choices, default=RoomStatus.VACANT_CLEAN)

    # Optional: housekeeping notes
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("tenant", "number")

    def __str__(self):
        return f"{self.number} ({self.tenant})"


class RoomStatusLog(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="room_status_logs")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="status_logs")
    old_status = models.CharField(max_length=32, choices=RoomStatus.choices)
    new_status = models.CharField(max_length=32, choices=RoomStatus.choices)
    reason = models.CharField(max_length=255, blank=True, default="")
    changed_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]


class RoomBlockReason(models.TextChoices):
    OUT_OF_ORDER = "out_of_order", "Out of Order"
    MAINTENANCE = "maintenance", "Maintenance"
    OTHER = "other", "Other"


class RoomBlock(models.Model):
    """
    Used by availability engine.
    If a room is out-of-order (or blocked), availability queries must exclude it.
    """
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="room_blocks")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="blocks")
    reason = models.CharField(max_length=32, choices=RoomBlockReason.choices)
    note = models.CharField(max_length=255, blank=True, default="")
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)  # open-ended block allowed
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-start_at"]

    def close(self, end_at=None):
        self.is_active = False
        self.end_at = end_at or timezone.now()
        self.save(update_fields=["is_active", "end_at"])
