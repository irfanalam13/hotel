from __future__ import annotations

from django.db.models import QuerySet

from .models import RatePlan, Room, RoomType


def list_room_types(*, organization, property_id=None) -> QuerySet:
    qs = RoomType.objects.filter(organization=organization)
    if property_id:
        qs = qs.filter(property_id=property_id)
    return qs


def list_rooms(*, organization, property_id=None, room_type_id=None) -> QuerySet:
    qs = Room.objects.filter(organization=organization).select_related("room_type")
    if property_id:
        qs = qs.filter(property_id=property_id)
    if room_type_id:
        qs = qs.filter(room_type_id=room_type_id)
    return qs


def list_rate_plans(*, organization, property_id=None) -> QuerySet:
    qs = RatePlan.objects.filter(organization=organization).select_related("room_type")
    if property_id:
        qs = qs.filter(property_id=property_id)
    return qs


def default_rate_for(room_type: RoomType):
    """Default nightly rate: the room type's default rate plan, else base rate."""
    plan = (
        RatePlan.all_objects.filter(room_type=room_type, is_active=True, is_default=True)
        .order_by("created_at")
        .first()
    )
    return plan.nightly_rate if plan else room_type.base_rate
