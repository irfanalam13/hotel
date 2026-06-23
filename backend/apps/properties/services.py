from __future__ import annotations

from django.db import transaction

from apps.common.exceptions import ConflictError, ValidationError
from apps.common.utils import unique_slugify

from .models import Property
from .selectors import count_properties


@transaction.atomic
def create_property(*, organization, name: str, code: str | None = None, **fields) -> Property:
    # Enforce the plan's property quota.
    if count_properties(organization=organization) >= organization.max_properties:
        raise ValidationError(
            f"Property limit reached for plan '{organization.plan}' "
            f"({organization.max_properties}). Upgrade to add more."
        )

    code = code or unique_slugify(
        name,
        exists=lambda s: Property.all_objects.filter(organization=organization, code=s).exists(),
    )
    if Property.all_objects.filter(organization=organization, code=code).exists():
        raise ConflictError(f"Property code '{code}' already exists in this organization.")

    return Property.objects.create(organization=organization, name=name, code=code, **fields)


@transaction.atomic
def update_property(*, instance: Property, **fields) -> Property:
    allowed = {
        "name", "address", "city", "country", "phone", "email",
        "timezone", "currency", "star_rating", "is_active",
    }
    changed = []
    for key, value in fields.items():
        if key in allowed:
            setattr(instance, key, value)
            changed.append(key)
    if changed:
        instance.save(update_fields=changed + ["updated_at"])
    return instance


@transaction.atomic
def archive_property(*, instance: Property) -> None:
    instance.delete()  # soft delete
