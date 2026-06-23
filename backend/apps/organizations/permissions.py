from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.rbac.constants import Perm

from .selectors import get_active_membership


class IsOrganizationMember(BasePermission):
    """Object-level: request.user is an active member of the Organization obj."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return get_active_membership(organization=obj, user=request.user) is not None


class CanManageOrganization(BasePermission):
    """Object-level: member holds ORG_MANAGE on the Organization obj."""

    message = "You cannot manage this organization."

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        membership = get_active_membership(organization=obj, user=request.user)
        return membership is not None and Perm.ORG_MANAGE in membership.role.permission_codes
