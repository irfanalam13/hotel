"""
Generic, domain-agnostic DRF permissions.

Role/membership-aware permissions live in ``apps.rbac.permissions``; this
module only holds primitives reused everywhere.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsTenantResolved(BasePermission):
    """Require an authenticated user *and* a resolved tenant on the request."""

    message = "An active organization (tenant) is required for this request."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request, "organization", None) is not None
        )


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
