from __future__ import annotations

from django.db.models import QuerySet

from .models import Membership, Organization


def get_organization_by_slug(slug: str) -> Organization | None:
    return Organization.objects.filter(slug=slug, is_active=True).first()


def organizations_for_user(user) -> QuerySet:
    return Organization.objects.filter(
        memberships__user=user, memberships__is_active=True
    ).distinct()


def list_members(organization) -> QuerySet:
    return (
        Membership.objects.filter(organization=organization)
        .select_related("user", "role")
        .prefetch_related("properties")
    )


def get_active_membership(*, organization, user) -> Membership | None:
    if organization is None or user is None or not getattr(user, "is_authenticated", False):
        return None
    return (
        Membership.objects.filter(organization=organization, user=user, is_active=True)
        .select_related("role")
        .first()
    )


def get_request_membership(request) -> Membership | None:
    """
    Membership for the current request's (organization, user), memoised on the
    request. Resolved lazily because JWT auth runs at view dispatch (after
    middleware), so ``request.user`` is only reliable here.
    """
    cached = getattr(request, "_membership_cache", "unset")
    if cached != "unset":
        return cached
    membership = get_active_membership(
        organization=getattr(request, "organization", None), user=getattr(request, "user", None)
    )
    request._membership_cache = membership
    return membership
