from __future__ import annotations

from django.db import transaction

from apps.common.exceptions import ValidationError

from .models import Guest, GuestDocument


@transaction.atomic
def create_guest(*, organization, property, first_name: str, **fields) -> Guest:
    if property.organization_id != organization.id:
        raise ValidationError("Property does not belong to this organization.")
    return Guest.objects.create(
        organization=organization, property=property, first_name=first_name, **fields
    )


@transaction.atomic
def update_guest(*, guest: Guest, **fields) -> Guest:
    allowed = {
        "first_name", "last_name", "email", "phone",
        "nationality", "address", "date_of_birth", "notes",
    }
    changed = [k for k in fields if k in allowed]
    for key in changed:
        setattr(guest, key, fields[key])
    if changed:
        guest.save(update_fields=changed + ["updated_at"])
    return guest


@transaction.atomic
def add_document(*, guest: Guest, doc_type: str, **fields) -> GuestDocument:
    return GuestDocument.objects.create(
        organization=guest.organization, guest=guest, doc_type=doc_type, **fields
    )
