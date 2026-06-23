from rest_framework.permissions import BasePermission


class IsSelfOrStaff(BasePermission):
    """Object-level: a user may act on their own record; staff on anyone's."""

    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or obj == request.user)
