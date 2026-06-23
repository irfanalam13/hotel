"""Write-side use cases for accounts. All mutations go through here."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from apps.common.exceptions import ConflictError, ValidationError

User = get_user_model()


def _validate_password(password: str, user=None) -> None:
    try:
        validate_password(password, user)
    except DjangoValidationError as exc:
        raise ValidationError("; ".join(exc.messages))


@transaction.atomic
def create_user(*, email: str, password: str, full_name: str = "", phone: str = "", **extra) -> User:
    if User.objects.filter(email__iexact=email).exists():
        raise ConflictError("A user with this email already exists.")
    _validate_password(password)
    return User.objects.create_user(
        email=email, password=password, full_name=full_name, phone=phone, **extra
    )


@transaction.atomic
def update_profile(*, user: User, full_name: str | None = None, phone: str | None = None) -> User:
    fields = []
    if full_name is not None:
        user.full_name = full_name
        fields.append("full_name")
    if phone is not None:
        user.phone = phone
        fields.append("phone")
    if fields:
        user.save(update_fields=fields + ["updated_at"])
    return user


@transaction.atomic
def change_password(*, user: User, current_password: str, new_password: str) -> User:
    if not user.check_password(current_password):
        raise ValidationError("Current password is incorrect.")
    _validate_password(new_password, user)
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    return user
