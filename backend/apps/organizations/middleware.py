"""
Tenant resolver middleware.

Binds the active :class:`Organization` to ``request.organization`` and to the
thread/async-local context (so tenant-scoped managers filter automatically).

Resolution order:
    1. Subdomain  -> ``<slug>.example.com``
    2. Header     -> ``X-Org-Slug: <slug>``
    3. Query arg  -> ``?org=<slug>``

Resolution is permissive: if no tenant is supplied the request still proceeds
with ``request.organization = None`` (e.g. listing the orgs you belong to).
Endpoints that *require* a tenant enforce it via RBAC permissions. Membership
is resolved later/lazily because JWT auth runs at view dispatch.
"""
from __future__ import annotations

from django.conf import settings

from apps.common.context import clear_current_organization, set_current_organization

from .selectors import get_organization_by_slug


class TenantResolverMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_prefixes = tuple(getattr(settings, "TENANT_PUBLIC_PATH_PREFIXES", ()))
        self.header = getattr(settings, "TENANT_HEADER", "X-Org-Slug")
        self.query_param = getattr(settings, "TENANT_QUERY_PARAM", "org")

    def __call__(self, request):
        request.organization = None
        token = None

        if not request.path.startswith(self.public_prefixes):
            slug = self._extract_slug(request)
            if slug:
                organization = get_organization_by_slug(slug)
                if organization is not None:
                    request.organization = organization
                    token = set_current_organization(organization)

        try:
            return self.get_response(request)
        finally:
            clear_current_organization(token)

    def _extract_slug(self, request) -> str | None:
        host = (request.get_host() or "").split(":")[0].lower()
        labels = host.split(".")
        # Treat a 3+ label host as <slug>.<domain>.<tld> (skip bare/localhost).
        if len(labels) >= 3 and labels[0] not in ("www", "api"):
            return labels[0]
        header_key = f"HTTP_{self.header.upper().replace('-', '_')}"
        return request.META.get(header_key) or request.GET.get(self.query_param)
