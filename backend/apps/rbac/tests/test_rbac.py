from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.organizations.services import create_organization
from apps.rbac.constants import ALL_PERMISSIONS, Perm, Role, SYSTEM_ROLE_TEMPLATES
from apps.rbac.models import Role as RoleModel
from apps.rbac import services

User = get_user_model()


class RbacProvisioningTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@acme.test", password="pw-strong-123")
        self.org = create_organization(name="Acme Hotels", owner=self.owner)

    def test_system_roles_provisioned_for_new_org(self):
        codes = set(RoleModel.objects.filter(organization=self.org).values_list("code", flat=True))
        self.assertEqual(codes, set(SYSTEM_ROLE_TEMPLATES))

    def test_owner_role_has_all_permissions(self):
        owner_role = RoleModel.objects.get(organization=self.org, code=Role.OWNER)
        self.assertEqual(owner_role.permission_codes, set(ALL_PERMISSIONS))

    def test_housekeeping_is_minimal(self):
        hk = RoleModel.objects.get(organization=self.org, code=Role.HOUSEKEEPING)
        self.assertEqual(
            hk.permission_codes,
            {Perm.PROPERTY_VIEW, Perm.ROOM_VIEW, Perm.RESERVATION_VIEW},
        )

    def test_cannot_delete_system_role(self):
        owner_role = RoleModel.objects.get(organization=self.org, code=Role.OWNER)
        with self.assertRaises(Exception):
            services.delete_role(role=owner_role)

    def test_create_and_edit_custom_role(self):
        role = services.create_role(
            organization=self.org, code="night_audit", name="Night Audit",
            permissions=[Perm.PROPERTY_VIEW, Perm.AUDIT_VIEW],
        )
        self.assertEqual(role.code, "NIGHT_AUDIT")
        self.assertEqual(role.permission_codes, {Perm.PROPERTY_VIEW, Perm.AUDIT_VIEW})
        services.set_role_permissions(role=role, permissions=[Perm.PROPERTY_VIEW])
        self.assertEqual(role.permission_codes, {Perm.PROPERTY_VIEW})
