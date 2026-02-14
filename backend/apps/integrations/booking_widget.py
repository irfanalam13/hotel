from django.utils import timezone
from decimal import Decimal

from apps.reservations.models import Reservation
from apps.guests.models import Guest

def create_widget_booking(*, tenant_id, payload: dict):
    """
    Minimal: creates guest + reservation in 'inquiry' or 'booked'.
    You can connect availability checks from reservations app.
    """
    guest, _ = Guest.objects.get_or_create(
        tenant_id=tenant_id,
        email=payload.get("email", "").strip().lower(),
        defaults={
            "full_name": payload.get("name", "").strip(),
            "phone": payload.get("phone", "").strip(),
        },
    )

    status = payload.get("status") or "inquiry"

    res = Reservation.objects.create(
        tenant_id=tenant_id,
        guest=guest,
        room_type_id=payload["room_type_id"],
        check_in=payload["check_in"],
        check_out=payload["check_out"],
        adults=int(payload.get("adults", 1)),
        children=int(payload.get("children", 0)),
        status=status,
        source="web_widget",
        notes=payload.get("notes", ""),
        # store expected price if you want:
        quoted_total=Decimal(str(payload.get("quoted_total", "0") or "0")),
    )
    return res
