from __future__ import annotations

from django.db import transaction

from apps.common.exceptions import ConflictError, NotFound, ValidationError
from apps.common.utils import unique_slugify
from apps.rbac.constants import DEFAULT_OWNER_ROLE
from apps.rbac.models import Role
from apps.rbac.services import provision_default_roles

from .models import Membership, Organization


@transaction.atomic
def create_organization(*, name: str, owner, slug: str | None = None, plan: str = Organization.Plan.FREE, **extra) -> Organization:
    """
    Create a tenant, provision its system roles, and enroll ``owner`` as OWNER.
    This is the single entry point that guarantees every org has RBAC roles and
    at least one owner.
    """
    slug = slug or unique_slugify(name, exists=lambda s: Organization.objects.filter(slug=s).exists())
    if Organization.objects.filter(slug=slug).exists():
        raise ConflictError(f"Organization slug '{slug}' is already taken.")

    organization = Organization.objects.create(name=name, slug=slug, plan=plan, **extra)
    provision_default_roles(organization=organization)

    owner_role = Role.objects.get(organization=organization, code=DEFAULT_OWNER_ROLE)
    Membership.objects.create(
        organization=organization, user=owner, role=owner_role, is_default=True
    )
    return organization


@transaction.atomic
def add_member(*, organization, user, role_code: str, invited_by=None, properties=None) -> Membership:
    if Membership.objects.filter(organization=organization, user=user).exists():
        raise ConflictError("User is already a member of this organization.")
    try:
        role = Role.objects.get(organization=organization, code=role_code.upper())
    except Role.DoesNotExist:
        raise NotFound(f"Role '{role_code}' does not exist in this organization.")

    membership = Membership.objects.create(
        organization=organization, user=user, role=role, invited_by=invited_by
    )
    if properties:
        membership.properties.set(properties)
    return membership


@transaction.atomic
def invite_member(*, organization, email: str, role_code: str, full_name: str = "", invited_by=None) -> Membership:
    """
    Add a member by email. If no account exists yet, a placeholder user is
    created with an unusable password (they set it via the invite/reset flow).
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        user = User.objects.create_user(email=email, password=None, full_name=full_name)
    return add_member(
        organization=organization, user=user, role_code=role_code, invited_by=invited_by
    )


@transaction.atomic
def change_member_role(*, membership: Membership, role_code: str) -> Membership:
    try:
        role = Role.objects.get(organization=membership.organization, code=role_code.upper())
    except Role.DoesNotExist:
        raise NotFound(f"Role '{role_code}' does not exist in this organization.")

    if membership.role.code == DEFAULT_OWNER_ROLE and role.code != DEFAULT_OWNER_ROLE:
        _guard_last_owner(membership)
    membership.role = role
    membership.save(update_fields=["role", "updated_at"])
    return membership


@transaction.atomic
def remove_member(*, membership: Membership) -> None:
    if membership.role.code == DEFAULT_OWNER_ROLE:
        _guard_last_owner(membership)
    membership.delete()


def _guard_last_owner(membership: Membership) -> None:
    owners = Membership.objects.filter(
        organization=membership.organization, role__code=DEFAULT_OWNER_ROLE, is_active=True
    ).exclude(id=membership.id)
    if not owners.exists():
        raise ValidationError("An organization must always have at least one owner.")
