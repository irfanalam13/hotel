"""Small shared helpers."""
from __future__ import annotations

import secrets

from django.utils.text import slugify


def generate_token(nbytes: int = 32) -> str:
    """URL-safe random token (invites, API keys, etc.)."""
    return secrets.token_urlsafe(nbytes)


def unique_slugify(value: str, *, exists, max_length: int = 50) -> str:
    """
    Slugify ``value`` and guarantee uniqueness via the ``exists(slug)`` predicate
    (returns True if a slug is already taken). Appends ``-2``, ``-3``, ...
    """
    base = slugify(value)[:max_length] or "item"
    candidate = base
    counter = 2
    while exists(candidate):
        suffix = f"-{counter}"
        candidate = f"{base[: max_length - len(suffix)]}{suffix}"
        counter += 1
    return candidate
