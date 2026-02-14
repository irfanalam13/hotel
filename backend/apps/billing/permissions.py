from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsHotelStaff(BasePermission):
    """
    Assumes request.user has tenant-scoped access already.
    Replace logic with your Month 1 roles system.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class IsManagerForRefundApproval(BasePermission):
    def has_permission(self, request, view):
        # Replace with role check: manager/admin
        return request.user and request.user.is_authenticated and request.user.is_staff
