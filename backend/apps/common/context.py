"""
Request-scoped tenant/user context.

Uses :class:`contextvars.ContextVar` (not ``threading.local``) so the active
tenant is correctly isolated across async views and Celery tasks. The tenant
resolver middleware binds the current Organization here; tenant-scoped model
managers read it to transparently filter querysets by tenant.
"""
from __future__ import annotations

import contextvars
from contextlib import contextmanager

_current_organization: contextvars.ContextVar = contextvars.ContextVar(
    "current_organization", default=None
)
_current_user: contextvars.ContextVar = contextvars.ContextVar(
    "current_user", default=None
)


def set_current_organization(organization):
    """Bind the active tenant. Returns a token for later reset."""
    return _current_organization.set(organization)


def get_current_organization():
    return _current_organization.get()


def set_current_user(user):
    return _current_user.set(user)


def get_current_user():
    return _current_user.get()


def clear_current_organization(token=None):
    if token is not None:
        _current_organization.reset(token)
    else:
        _current_organization.set(None)


@contextmanager
def use_tenant(organization):
    """Temporarily bind a tenant (handy in services, tests and Celery tasks)."""
    token = _current_organization.set(organization)
    try:
        yield organization
    finally:
        _current_organization.reset(token)
