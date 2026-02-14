import csv
from datetime import datetime
from apps.reservations.models import Reservation
from apps.guests.models import Guest

def parse_date(val: str):
    return datetime.strptime(val.strip(), "%Y-%m-%d").date()

def import_ota_csv(*, tenant_id, file_obj, source_name="OTA_CSV"):
    """
    Expected columns:
    guest_name,email,phone,room_type_id,check_in,check_out,adults,children,status,notes
    """
    reader = csv.DictReader((line.decode("utf-8") for line in file_obj.readlines()))
    created = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            email = (row.get("email") or "").strip().lower()
            guest, _ = Guest.objects.get_or_create(
                tenant_id=tenant_id,
                email=email,
                defaults={
                    "full_name": (row.get("guest_name") or "").strip(),
                    "phone": (row.get("phone") or "").strip(),
                },
            )

            Reservation.objects.create(
                tenant_id=tenant_id,
                guest=guest,
                room_type_id=row["room_type_id"],
                check_in=parse_date(row["check_in"]),
                check_out=parse_date(row["check_out"]),
                adults=int(row.get("adults") or 1),
                children=int(row.get("children") or 0),
                status=(row.get("status") or "booked"),
                source=source_name,
                notes=(row.get("notes") or ""),
            )
            created += 1
        except Exception as e:
            errors.append({"line": i, "error": str(e), "row": row})

    return {"created": created, "errors": errors}
