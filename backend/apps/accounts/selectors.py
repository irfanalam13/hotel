"""Read-side queries for accounts (no side effects)."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

User = get_user_model()


def get_user_by_email(email: str):
    return User.objects.filter(email__iexact=email).first()


def list_users() -> QuerySet:
    return User.objects.all()


def get_user(user_id) -> User:
    return User.objects.get(id=user_id)
