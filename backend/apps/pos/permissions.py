from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsPOSStaff(BasePermission):
    """
    Real-life: cashier/waiter can create orders and settlements.
    Use your accounts roles/permissions; below is a safe default.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsPOSManager(BasePermission):
    """
    Manager approval: void/refund/discount decisions.
    Replace with your role check (e.g. request.user.role == 'manager').
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))
