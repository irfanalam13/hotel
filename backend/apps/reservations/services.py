"""
Reservation lifecycle (write side).

Double-booking prevention strategy (spec: "using database transactions"):
``create_reservation`` / ``modify_reservation`` run inside ``transaction.atomic``
and ``select_for_update()`` the candidate room rows. Concurrent bookings for the
same rooms therefore serialize: the second transaction blocks on the row locks,
then re-reads committed bookings and finds the room taken. The overlap re-check
runs *after* the lock is held, so two requests can never both win the same room.
"""
from __future__ import annotations

from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import ConflictError, NotFound, ValidationError
from apps.rooms.models import Room, RoomType
from apps.rooms.selectors import default_rate_for

from .models import (
    BLOCKING_STATUSES,
    Reservation,
    ReservationCharge,
    ReservationGuest,
    ReservationRoom,
    ReservationStatus,
    ReservationStatusLog,
)
from .selectors import unavailable_room_ids


def _generate_code(organization) -> str:
    n = Reservation.all_objects.filter(organization=organization).count() + 1
    return f"RSV-{n:06d}"


def _log(reservation, from_status, to_status, by_user, note=""):
    ReservationStatusLog.objects.create(
        reservation=reservation, from_status=from_status,
        to_status=to_status, by_user=by_user, note=note,
    )


@transaction.atomic
def create_reservation(
    *, organization, property, check_in: date, check_out: date, room_requests,
    primary_guest=None, adults: int = 1, children: int = 0,
    source: str = "front_desk", special_requests: str = "", by_user=None,
) -> Reservation:
    if check_out <= check_in:
        raise ValidationError("check_out must be after check_in.")
    if not room_requests:
        raise ValidationError("At least one room is required.")
    if property.organization_id != organization.id:
        raise ValidationError("Property does not belong to this organization.")

    nights = (check_out - check_in).days

    # Lock all bookable rooms of the property for the duration of the txn.
    locked_rooms = list(
        Room.objects.all_tenants()
        .select_for_update()
        .filter(organization=organization, property=property, is_active=True)
        .exclude(status=Room.Status.OUT_OF_ORDER)
    )
    rooms_by_id = {r.id: r for r in locked_rooms}
    taken = unavailable_room_ids(property=property, check_in=check_in, check_out=check_out)

    assigned: set = set()
    plan = []  # (room_type, room, rate, adults, children)
    for req in room_requests:
        room_type = (
            RoomType.objects.all_tenants()
            .filter(organization=organization, property=property, id=req["room_type_id"])
            .first()
        )
        if room_type is None:
            raise NotFound("Room type not found for this property.")

        requested_room_id = req.get("room_id")
        if requested_room_id:
            room = rooms_by_id.get(_as_uuid(requested_room_id, rooms_by_id))
            if room is None:
                raise NotFound("Requested room not found or not bookable.")
            if room.room_type_id != room_type.id:
                raise ValidationError("Requested room does not match the room type.")
            if room.id in taken or room.id in assigned:
                raise ConflictError(f"Room {room.number} is not available for these dates.")
        else:
            room = next(
                (r for r in locked_rooms
                 if r.room_type_id == room_type.id and r.id not in taken and r.id not in assigned),
                None,
            )
            if room is None:
                raise ConflictError(f"No availability for room type '{room_type.name}'.")

        assigned.add(room.id)
        rate = req.get("nightly_rate")
        if rate is None:
            rate = default_rate_for(room_type)
        plan.append((room_type, room, rate, req.get("adults", 1), req.get("children", 0)))

    reservation = Reservation.objects.create(
        organization=organization, property=property, code=_generate_code(organization),
        status=ReservationStatus.BOOKED, primary_guest=primary_guest,
        check_in=check_in, check_out=check_out, adults=adults, children=children,
        source=source, special_requests=special_requests,
        currency=property.currency or organization.currency,
    )

    total = 0
    for room_type, room, rate, line_adults, line_children in plan:
        amount = rate * nights
        ReservationRoom.objects.create(
            organization=organization, reservation=reservation, room_type=room_type,
            room=room, nightly_rate=rate, nights=nights, amount=amount,
            adults=line_adults, children=line_children,
        )
        total += amount

    reservation.total_amount = total
    reservation.save(update_fields=["total_amount", "updated_at"])

    if primary_guest is not None:
        ReservationGuest.objects.create(
            reservation=reservation, guest=primary_guest, is_primary=True
        )
    _log(reservation, "", ReservationStatus.BOOKED, by_user, "Reservation created")
    return reservation


def _as_uuid(value, rooms_by_id):
    """Match a string/UUID room id against the locked rooms map keys."""
    for key in rooms_by_id:
        if str(key) == str(value):
            return key
    return value


@transaction.atomic
def modify_reservation(
    *, reservation: Reservation, check_in: date | None = None, check_out: date | None = None,
    adults: int | None = None, children: int | None = None,
    special_requests: str | None = None, internal_notes: str | None = None, by_user=None,
) -> Reservation:
    if reservation.status not in (ReservationStatus.INQUIRY, ReservationStatus.BOOKED):
        raise ValidationError("Only inquiry or booked reservations can be modified.")

    new_in = check_in or reservation.check_in
    new_out = check_out or reservation.check_out
    if new_out <= new_in:
        raise ValidationError("check_out must be after check_in.")

    dates_changed = (new_in, new_out) != (reservation.check_in, reservation.check_out)
    if dates_changed:
        # Lock this reservation's rooms, re-validate availability for new dates.
        lines = list(reservation.rooms.select_for_update().all())
        taken = unavailable_room_ids(
            property=reservation.property, check_in=new_in, check_out=new_out,
            exclude_reservation_id=reservation.id,
        )
        nights = (new_out - new_in).days
        for line in lines:
            if line.room_id and line.room_id in taken:
                raise ConflictError("An assigned room is not available for the new dates.")
            line.nights = nights
            line.amount = line.nightly_rate * nights
            line.save(update_fields=["nights", "amount", "updated_at"])
        reservation.check_in = new_in
        reservation.check_out = new_out
        reservation.total_amount = sum((l.amount for l in lines), 0)

    if adults is not None:
        reservation.adults = adults
    if children is not None:
        reservation.children = children
    if special_requests is not None:
        reservation.special_requests = special_requests
    if internal_notes is not None:
        reservation.internal_notes = internal_notes

    reservation.save()
    _log(reservation, reservation.status, reservation.status, by_user, "Reservation modified")
    return reservation


@transaction.atomic
def cancel_reservation(*, reservation: Reservation, by_user=None, reason: str = "") -> Reservation:
    if reservation.status in (ReservationStatus.CHECKED_OUT, ReservationStatus.CANCELLED):
        raise ValidationError(f"Cannot cancel a {reservation.status} reservation.")
    previous = reservation.status
    reservation.status = ReservationStatus.CANCELLED
    reservation.save(update_fields=["status", "updated_at"])
    _log(reservation, previous, ReservationStatus.CANCELLED, by_user, reason or "Cancelled")
    return reservation


@transaction.atomic
def check_in(*, reservation: Reservation, by_user=None) -> Reservation:
    if reservation.status != ReservationStatus.BOOKED:
        raise ValidationError("Only booked reservations can be checked in.")
    lines = list(reservation.rooms.all())
    if any(line.room_id is None for line in lines):
        raise ValidationError("Every room must be assigned before check-in.")

    reservation.status = ReservationStatus.CHECKED_IN
    reservation.checked_in_at = timezone.now()
    reservation.save(update_fields=["status", "checked_in_at", "updated_at"])
    for line in lines:
        Room.objects.filter(id=line.room_id).update(status=Room.Status.OCCUPIED)
    _log(reservation, ReservationStatus.BOOKED, ReservationStatus.CHECKED_IN, by_user, "Checked in")
    return reservation


@transaction.atomic
def check_out(*, reservation: Reservation, by_user=None) -> Reservation:
    if reservation.status != ReservationStatus.CHECKED_IN:
        raise ValidationError("Only checked-in reservations can be checked out.")
    reservation.status = ReservationStatus.CHECKED_OUT
    reservation.checked_out_at = timezone.now()
    reservation.save(update_fields=["status", "checked_out_at", "updated_at"])
    for line in reservation.rooms.all():
        if line.room_id:
            Room.objects.filter(id=line.room_id).update(status=Room.Status.VACANT_DIRTY)
    _log(reservation, ReservationStatus.CHECKED_IN, ReservationStatus.CHECKED_OUT, by_user, "Checked out")
    return reservation


@transaction.atomic
def add_charge(*, reservation: Reservation, kind: str, description: str, amount, posted_on=None) -> ReservationCharge:
    return ReservationCharge.objects.create(
        organization=reservation.organization, reservation=reservation,
        kind=kind, description=description, amount=amount,
        posted_on=posted_on or date.today(),
    )
