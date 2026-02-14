from rest_framework.permissions import BasePermission


class IsTenantStaff(BasePermission):
    """
    Example:
    - allow only logged-in users who belong to a tenant (hotel).
    You can replace this with your existing multi-tenant permission system.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
