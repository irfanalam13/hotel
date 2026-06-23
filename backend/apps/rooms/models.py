"""
Rooms domain: room types, physical rooms, rate plans and operational blocks.

Everything is tenant-scoped (``organization`` + soft delete + UUID + timestamps
via :class:`TenantScopedModel`) and additionally bound to a Property.
"""
from __future__ import annotations

import builtins

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantScopedModel


class RoomType(TenantScopedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="room_types"
    )
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=40)
    description = models.TextField(blank=True, default="")
    max_adults = models.PositiveSmallIntegerField(default=2)
    max_children = models.PositiveSmallIntegerField(default=0)
    base_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "code"], name="uniq_roomtype_code_per_property"
            )
        ]
        indexes = [models.Index(fields=["organization", "property"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @builtins.property
    def capacity(self) -> int:
        return self.max_adults + self.max_children


class Room(TenantScopedModel):
    class Status(models.TextChoices):
        VACANT_CLEAN = "vacant_clean", "Vacant Clean"
        VACANT_DIRTY = "vacant_dirty", "Vacant Dirty"
        OCCUPIED = "occupied", "Occupied"
        OUT_OF_ORDER = "out_of_order", "Out of Order"

    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="rooms"
    )
    room_type = models.ForeignKey(
        RoomType, on_delete=models.PROTECT, related_name="rooms"
    )
    number = models.CharField(max_length=20)
    floor = models.CharField(max_length=20, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.VACANT_CLEAN
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "number"], name="uniq_room_number_per_property"
            )
        ]
        indexes = [
            models.Index(fields=["organization", "property", "status"]),
            models.Index(fields=["property", "room_type"]),
        ]

    def __str__(self) -> str:
        return f"Room {self.number}"

    @builtins.property
    def is_bookable(self) -> bool:
        return self.is_active and self.status != self.Status.OUT_OF_ORDER


class RatePlan(TenantScopedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="rate_plans"
    )
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name="rate_plans"
    )
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=40)
    nightly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "code"], name="uniq_rateplan_code_per_property"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} @ {self.nightly_rate}"


class RoomBlock(TenantScopedModel):
    """
    A room taken out of inventory for a date range (maintenance / out-of-order).
    The availability engine excludes rooms with an overlapping active block.
    Date range is half-open ``[start_date, end_date)`` like reservations.
    """

    class Reason(models.TextChoices):
        OUT_OF_ORDER = "out_of_order", "Out of Order"
        MAINTENANCE = "maintenance", "Maintenance"
        OTHER = "other", "Other"

    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="room_blocks"
    )
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="blocks")
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    note = models.CharField(max_length=255, blank=True, default="")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [models.Index(fields=["room", "start_date", "end_date"])]

    def __str__(self) -> str:
        return f"Block {self.room_id} [{self.start_date}..{self.end_date})"
