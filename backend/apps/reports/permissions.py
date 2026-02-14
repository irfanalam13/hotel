from rest_framework.permissions import BasePermission

class IsTenantOwnerOrManager(BasePermission):
    """
    Plug into your role system:
    - allow hotel owner / GM / accountant
    """
    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        # Adjust to your roles implementation
        return getattr(u, "is_owner", False) or getattr(u, "is_manager", False) or getattr(u, "is_accountant", False)
