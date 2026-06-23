"""Property permissions reuse the central RBAC gate."""
from apps.rbac.constants import Perm
from apps.rbac.permissions import HasOrgPermission

__all__ = ["HasOrgPermission", "Perm"]
