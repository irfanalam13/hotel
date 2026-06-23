from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound as DRFNotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.rbac.constants import Perm
from apps.rbac.permissions import HasOrgPermission

from . import selectors, services
from .models import Membership
from .permissions import CanManageOrganization
from .serializers import (
    MemberInviteSerializer,
    MemberRoleUpdateSerializer,
    MembershipSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """The organizations the caller belongs to. Creating one makes you its owner."""

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return selectors.Organization.objects.none()
        return selectors.organizations_for_user(self.request.user)

    def get_permissions(self):
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), CanManageOrganization()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = services.create_organization(owner=request.user, **serializer.validated_data)
        return Response(OrganizationSerializer(organization).data, status=status.HTTP_201_CREATED)


class MembershipViewSet(viewsets.ViewSet):
    """
    Members of the *currently resolved* organization (via ``X-Org-Slug``).
    Read needs MEMBER_VIEW; mutations need MEMBER_MANAGE.
    """

    permission_classes = [HasOrgPermission]
    required_permissions = {
        "GET": {Perm.MEMBER_VIEW},
        "POST": {Perm.MEMBER_MANAGE},
        "PATCH": {Perm.MEMBER_MANAGE},
        "DELETE": {Perm.MEMBER_MANAGE},
    }

    def _get_membership(self, pk) -> Membership:
        membership = (
            Membership.objects.filter(organization=self.request.organization, id=pk)
            .select_related("user", "role")
            .first()
        )
        if membership is None:
            raise DRFNotFound("Member not found in this organization.")
        return membership

    def list(self, request):
        members = selectors.list_members(request.organization)
        return Response(MembershipSerializer(members, many=True).data)

    @action(detail=False, methods=["post"])
    def invite(self, request):
        serializer = MemberInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = services.invite_member(
            organization=request.organization, invited_by=request.user, **serializer.validated_data
        )
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="role")
    def set_role(self, request, pk=None):
        serializer = MemberRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = services.change_member_role(
            membership=self._get_membership(pk), role_code=serializer.validated_data["role_code"]
        )
        return Response(MembershipSerializer(membership).data)

    def destroy(self, request, pk=None):
        services.remove_member(membership=self._get_membership(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)
