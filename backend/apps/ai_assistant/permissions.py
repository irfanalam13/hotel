from rest_framework.permissions import BasePermission

class IsTenantStaff(BasePermission):
    """
    Assumes your auth already sets request.tenant and user is tenant-scoped.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        # adapt to your role system
        return getattr(u, "is_superuser", False) or getattr(u, "is_staff", False) or getattr(u, "role", "") in {"manager", "admin"}
