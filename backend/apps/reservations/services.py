from apps.properties.models import Room
from .models import Reservation

ACTIVE_STATUSES = {Reservation.Status.BOOKED, Reservation.Status.CHECKED_IN}

def get_reserved_room_ids(property_id, start, end):
    qs = Reservation.objects.filter(
        property_id=property_id,
        status__in=ACTIVE_STATUSES,
        check_in__lt=end,
        check_out__gt=start,
        room__isnull=False,
    ).values_list("room_id", flat=True)
    return set(qs)

def availability_by_room_type(property_id, start, end):
    """
    Returns list of:
    {
      room_type_id, room_type_name,
      total_rooms, out_of_order, available
    }
    """
    from apps.properties.models import RoomType

    reserved_room_ids = get_reserved_room_ids(property_id, start, end)

    result = []
    for rt in RoomType.objects.filter(property_id=property_id):
        rooms = Room.objects.filter(property_id=property_id, room_type=rt, is_active=True)
        total = rooms.count()
        ooo = rooms.filter(housekeeping_status=Room.HousekeepingStatus.OOO).count()

        usable_rooms = rooms.exclude(housekeeping_status=Room.HousekeepingStatus.OOO)
        available = usable_rooms.exclude(id__in=reserved_room_ids).count()

        result.append({
            "room_type_id": str(rt.id),
            "room_type_name": rt.name,
            "total_rooms": total,
            "out_of_order": ooo,
            "available": available,
        })
    return result

def available_rooms(property_id, room_type_id, start, end):
    reserved_room_ids = get_reserved_room_ids(property_id, start, end)
    return Room.objects.filter(
        property_id=property_id,
        room_type_id=room_type_id,
        is_active=True,
    ).exclude(
        housekeeping_status=Room.HousekeepingStatus.OOO
    ).exclude(
        id__in=reserved_room_ids
    ).order_by("number")
