"""Read-side queries, including the availability engine."""
from __future__ import annotations

from datetime import date

from django.db.models import QuerySet

from apps.rooms.models import Room, RoomBlock

from .models import BLOCKING_STATUSES, Reservation, ReservationRoom


def list_reservations(*, organization, property_id=None, status=None) -> QuerySet:
    qs = (
        Reservation.objects.filter(organization=organization)
        .select_related("property", "primary_guest")
        .prefetch_related("rooms")
    )
    if property_id:
        qs = qs.filter(property_id=property_id)
    if status:
        qs = qs.filter(status=status)
    return qs


def _booked_room_ids(*, property, check_in: date, check_out: date, exclude_reservation_id=None) -> set:
    qs = ReservationRoom.objects.all_tenants().filter(
        reservation__property=property,
        reservation__status__in=BLOCKING_STATUSES,
        reservation__check_in__lt=check_out,
        reservation__check_out__gt=check_in,
        room__isnull=False,
    )
    if exclude_reservation_id:
        qs = qs.exclude(reservation_id=exclude_reservation_id)
    return set(qs.values_list("room_id", flat=True))


def _blocked_room_ids(*, property, check_in: date, check_out: date) -> set:
    return set(
        RoomBlock.objects.all_tenants()
        .filter(
            property=property,
            is_active=True,
            start_date__lt=check_out,
            end_date__gt=check_in,
        )
        .values_list("room_id", flat=True)
    )


def unavailable_room_ids(*, property, check_in: date, check_out: date, exclude_reservation_id=None) -> set:
    """Rooms that cannot be booked for the range (already booked OR blocked)."""
    return _booked_room_ids(
        property=property, check_in=check_in, check_out=check_out,
        exclude_reservation_id=exclude_reservation_id,
    ) | _blocked_room_ids(property=property, check_in=check_in, check_out=check_out)


def find_available_rooms(
    *, organization, property, check_in: date, check_out: date,
    room_type=None, exclude_reservation_id=None,
) -> QuerySet:
    rooms = (
        Room.objects.all_tenants()
        .filter(organization=organization, property=property, is_active=True)
        .exclude(status=Room.Status.OUT_OF_ORDER)
        .select_related("room_type")
    )
    if room_type is not None:
        rooms = rooms.filter(room_type=room_type)
    taken = unavailable_room_ids(
        property=property, check_in=check_in, check_out=check_out,
        exclude_reservation_id=exclude_reservation_id,
    )
    return rooms.exclude(id__in=taken).order_by("number")


def availability_summary(*, organization, property, check_in: date, check_out: date) -> list[dict]:
    """Available room count + nightly rate per room type for the date range."""
    from apps.rooms.selectors import default_rate_for
    from apps.rooms.models import RoomType

    available = find_available_rooms(
        organization=organization, property=property, check_in=check_in, check_out=check_out
    )
    by_type: dict = {}
    for room in available:
        by_type.setdefault(room.room_type_id, []).append(room)

    nights = (check_out - check_in).days
    summary = []
    for room_type in RoomType.objects.all_tenants().filter(organization=organization, property=property):
        rooms = by_type.get(room_type.id, [])
        rate = default_rate_for(room_type)
        summary.append(
            {
                "room_type_id": str(room_type.id),
                "room_type": room_type.name,
                "available": len(rooms),
                "nightly_rate": rate,
                "nights": nights,
                "total_price": rate * nights,
            }
        )
    return summary
