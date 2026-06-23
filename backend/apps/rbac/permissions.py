"""
RBAC-aware DRF permissions.

The tenant middleware binds ``request.organization`` and ``request.membership``.
These classes translate a member's role into a permission set and gate the view.

Views declare requirements via ``required_permissions`` — either a flat
iterable (applied to every method) or a dict keyed by HTTP method::

    class PropertyViewSet(...):
        required_permissions = {
            "GET": {Perm.PROPERTY_VIEW},
            "POST": {Perm.PROPERTY_MANAGE},
            "*": {Perm.PROPERTY_MANAGE},   # fallback for other methods
        }
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission

from .constants import ALL_PERMISSIONS


def get_request_permissions(request) -> set[str] | None:
    """
    Effective permission codes for the request, or ``None`` if unauthenticated.
    Superusers implicitly hold every permission. Result is memoised per request.
    """
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated):
        return None

    cached = getattr(request, "_rbac_permissions", None)
    if cached is not None:
        return cached

    if user.is_superuser:
        perms = set(ALL_PERMISSIONS)
    else:
        # Lazy import avoids an organizations <-> rbac import cycle at load time.
        from apps.organizations.selectors import get_request_membership

        membership = get_request_membership(request)
        if membership is None or membership.role_id is None:
            perms = set()
        else:
            perms = membership.role.permission_codes

    request._rbac_permissions = perms
    return perms


def _required_for_method(view, method: str) -> set[str]:
    # A view may compute requirements per action (e.g. POST actions that need
    # different permissions); that hook wins over the static declaration.
    if hasattr(view, "get_required_permissions"):
        return set(view.get_required_permissions())
    required = getattr(view, "required_permissions", None)
    if not required:
        return set()
    if isinstance(required, dict):
        codes = required.get(method, required.get("*", set()))
    else:
        codes = required
    return set(codes)


class IsOrgMember(BasePermission):
    """Authenticated and an active member of the resolved organization."""

    message = "You are not a member of this organization."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        from apps.organizations.selectors import get_request_membership

        return get_request_membership(request) is not None


class HasOrgPermission(BasePermission):
    """Gate the view by ``required_permissions`` (member must hold all of them)."""

    message = "You do not have the required permission for this action."

    def has_permission(self, request, view):
        required = _required_for_method(view, request.method)
        if not required:
            # No explicit requirement: fall back to membership.
            return IsOrgMember().has_permission(request, view)
        user_perms = get_request_permissions(request)
        if user_perms is None:
            return False
        return required.issubset(user_perms)
