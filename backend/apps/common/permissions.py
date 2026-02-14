from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedAndTenant(BasePermission):
    """
    Ensures request.user exists AND request.tenant is resolved.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request, "tenant", None))

class IsHotelOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "OWNER")

class IsManagerOrOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ["OWNER", "MANAGER"])

class StaffReadOnlyIfNotManager(BasePermission):
    """
    Staff can read, managers/owners can write.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.role in ["OWNER", "MANAGER"])



class IsPropertyStaff(BasePermission):
    """
    Simple real-life rule:
    - user must be authenticated
    - request must include X-PROPERTY-ID header
    - user must be staff of that property (for now we allow all authenticated users)
    Replace with real membership checks later.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        prop_id = request.headers.get("X-PROPERTY-ID")
        return bool(prop_id)

class HasPropertyObjectAccess(BasePermission):
    """
    Ensures object's property_id matches header X-PROPERTY-ID.
    """
    def has_object_permission(self, request, view, obj):
        prop_id = request.headers.get("X-PROPERTY-ID")
        if not prop_id:
            return False
        return str(getattr(obj, "property_id", "")) == str(prop_id)
