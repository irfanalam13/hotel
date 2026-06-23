"""
RBAC catalogue: the canonical set of permission codes and the system role
templates that map roles to permissions. These are the single source of truth
used to provision per-organization roles.
"""
from __future__ import annotations


class Perm:
    """Permission codes. Format: ``<domain>.<action>``."""

    ORG_VIEW = "organization.view"
    ORG_MANAGE = "organization.manage"

    MEMBER_VIEW = "member.view"
    MEMBER_MANAGE = "member.manage"

    ROLE_VIEW = "role.view"
    ROLE_MANAGE = "role.manage"

    PROPERTY_VIEW = "property.view"
    PROPERTY_MANAGE = "property.manage"

    # Phase 2 — core PMS domains.
    ROOM_VIEW = "room.view"
    ROOM_MANAGE = "room.manage"

    GUEST_VIEW = "guest.view"
    GUEST_MANAGE = "guest.manage"

    RESERVATION_VIEW = "reservation.view"
    RESERVATION_MANAGE = "reservation.manage"
    # Front-desk operations: check-in / check-out / room assignment.
    RESERVATION_OPERATE = "reservation.operate"

    AUDIT_VIEW = "audit.view"


# Human-readable catalogue (code -> label) for UIs and validation.
PERMISSION_CATALOG: dict[str, str] = {
    Perm.ORG_VIEW: "View organization",
    Perm.ORG_MANAGE: "Manage organization settings",
    Perm.MEMBER_VIEW: "View members",
    Perm.MEMBER_MANAGE: "Invite / manage members",
    Perm.ROLE_VIEW: "View roles",
    Perm.ROLE_MANAGE: "Manage roles & permissions",
    Perm.PROPERTY_VIEW: "View properties",
    Perm.PROPERTY_MANAGE: "Create / edit properties",
    Perm.ROOM_VIEW: "View rooms & room types",
    Perm.ROOM_MANAGE: "Manage rooms, room types & rate plans",
    Perm.GUEST_VIEW: "View guests",
    Perm.GUEST_MANAGE: "Create / edit guests",
    Perm.RESERVATION_VIEW: "View reservations",
    Perm.RESERVATION_MANAGE: "Create / modify / cancel reservations",
    Perm.RESERVATION_OPERATE: "Check-in / check-out / assign rooms",
    Perm.AUDIT_VIEW: "View audit log",
}

ALL_PERMISSIONS = frozenset(PERMISSION_CATALOG)
_VIEW_ONLY = frozenset(p for p in ALL_PERMISSIONS if p.endswith(".view"))

# Common operational bundles.
_PMS_OPS = frozenset({
    Perm.PROPERTY_VIEW,
    Perm.ROOM_VIEW,
    Perm.GUEST_VIEW, Perm.GUEST_MANAGE,
    Perm.RESERVATION_VIEW, Perm.RESERVATION_MANAGE, Perm.RESERVATION_OPERATE,
    Perm.ORG_VIEW,
})


class Role:
    """System role codes (the platform-level Super Admin maps to is_superuser)."""

    OWNER = "OWNER"                  # Organization owner (full control)
    ADMIN = "ADMIN"                  # Organization Admin
    MANAGER = "MANAGER"              # Property Manager
    RECEPTIONIST = "RECEPTIONIST"    # Front desk
    HOUSEKEEPING = "HOUSEKEEPING"    # Housekeeping staff
    MAINTENANCE = "MAINTENANCE"      # Maintenance staff
    ACCOUNTANT = "ACCOUNTANT"        # Accountant
    GUEST = "GUEST"                  # Guest (self-service, minimal)
    READ_ONLY = "READ_ONLY"


# Role template: code -> (display name, permission set).
SYSTEM_ROLE_TEMPLATES: dict[str, tuple[str, frozenset[str]]] = {
    Role.OWNER: ("Owner", ALL_PERMISSIONS),
    Role.ADMIN: ("Organization Admin", ALL_PERMISSIONS),
    Role.MANAGER: (
        "Property Manager",
        _PMS_OPS | {
            Perm.PROPERTY_MANAGE, Perm.ROOM_MANAGE,
            Perm.MEMBER_VIEW, Perm.ROLE_VIEW, Perm.AUDIT_VIEW,
        },
    ),
    Role.RECEPTIONIST: ("Receptionist", _PMS_OPS),
    Role.HOUSEKEEPING: (
        "Housekeeping Staff",
        frozenset({Perm.PROPERTY_VIEW, Perm.ROOM_VIEW, Perm.RESERVATION_VIEW}),
    ),
    Role.MAINTENANCE: (
        "Maintenance Staff",
        frozenset({Perm.PROPERTY_VIEW, Perm.ROOM_VIEW, Perm.ROOM_MANAGE}),
    ),
    Role.ACCOUNTANT: (
        "Accountant",
        frozenset({
            Perm.ORG_VIEW, Perm.PROPERTY_VIEW,
            Perm.RESERVATION_VIEW, Perm.AUDIT_VIEW,
        }),
    ),
    Role.GUEST: ("Guest", frozenset({Perm.RESERVATION_VIEW})),
    Role.READ_ONLY: ("Read Only", _VIEW_ONLY),
}

DEFAULT_OWNER_ROLE = Role.OWNER
