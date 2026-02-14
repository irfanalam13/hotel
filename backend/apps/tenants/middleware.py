from django.http import JsonResponse
from apps.tenants.models import Hotel
from apps.common.tenant import set_current_tenant, clear_current_tenant

PUBLIC_PATH_PREFIXES = (
    "/admin/",
    "/api/tenants/onboard/",
    "/api/accounts/auth/",
)

class TenantResolverMiddleware:
    """
    Resolves tenant from:
    1) Subdomain: <subdomain>.yourapp.com
    2) Header: X-Hotel-Code: <hotel_code>
    3) Query (fallback): ?hotel_code=
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or "/"

        # allow public endpoints without tenant
        if path.startswith(PUBLIC_PATH_PREFIXES):
            request.tenant = None
            return self.get_response(request)

        tenant = None

        host = (request.get_host() or "").split(":")[0].lower()
        parts = host.split(".")
        if len(parts) >= 3:
            subdomain = parts[0]
            tenant = Hotel.objects.filter(subdomain=subdomain, is_active=True).first()

        if tenant is None:
            code = request.headers.get("X-Hotel-Code") or request.GET.get("hotel_code")
            if code:
                tenant = Hotel.objects.filter(hotel_code=code, is_active=True).first()

        if tenant is None:
            return JsonResponse(
                {"detail": "Tenant not resolved. Provide subdomain or X-Hotel-Code."},
                status=400
            )

        request.tenant = tenant
        set_current_tenant(tenant)
        try:
            return self.get_response(request)
        finally:
            clear_current_tenant()
