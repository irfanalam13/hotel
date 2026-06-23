from __future__ import annotations

from django.db import transaction

from apps.common.exceptions import ConflictError, ValidationError
from apps.common.utils import unique_slugify

from .models import RatePlan, Room, RoomType


def _belongs_to_org(property, organization):
    if property.organization_id != organization.id:
        raise ValidationError("Property does not belong to this organization.")


@transaction.atomic
def create_room_type(*, organization, property, name: str, code: str | None = None, **fields) -> RoomType:
    _belongs_to_org(property, organization)
    code = code or unique_slugify(
        name,
        exists=lambda s: RoomType.all_objects.filter(property=property, code=s).exists(),
    )
    if RoomType.all_objects.filter(property=property, code=code).exists():
        raise ConflictError(f"Room type code '{code}' already exists for this property.")
    return RoomType.objects.create(organization=organization, property=property, name=name, code=code, **fields)


@transaction.atomic
def create_room(*, organization, property, room_type: RoomType, number: str, **fields) -> Room:
    _belongs_to_org(property, organization)
    if room_type.property_id != property.id:
        raise ValidationError("Room type must belong to the same property.")
    if Room.all_objects.filter(property=property, number=number).exists():
        raise ConflictError(f"Room '{number}' already exists for this property.")
    return Room.objects.create(
        organization=organization, property=property, room_type=room_type, number=number, **fields
    )


@transaction.atomic
def set_room_status(*, room: Room, status: str) -> Room:
    if status not in Room.Status.values:
        raise ValidationError(f"Invalid room status '{status}'.")
    room.status = status
    room.save(update_fields=["status", "updated_at"])
    return room


@transaction.atomic
def create_rate_plan(*, organization, property, room_type: RoomType, name: str, nightly_rate, code: str | None = None, is_default: bool = False) -> RatePlan:
    _belongs_to_org(property, organization)
    code = code or unique_slugify(
        name,
        exists=lambda s: RatePlan.all_objects.filter(property=property, code=s).exists(),
    )
    if is_default:
        RatePlan.objects.filter(room_type=room_type, is_default=True).update(is_default=False)
    return RatePlan.objects.create(
        organization=organization, property=property, room_type=room_type,
        name=name, code=code, nightly_rate=nightly_rate, is_default=is_default,
    )
