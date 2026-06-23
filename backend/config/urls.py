"""Root URL configuration — Phase 1 foundation routes only."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    # Liveness/readiness probe (public, no tenant required).
    path("api/health/", health, name="health"),
    # Auth (JWT).
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # OpenAPI schema + docs.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    # Foundation domain apps.
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/rbac/", include("apps.rbac.urls")),
    path("api/organizations/", include("apps.organizations.urls")),
    path("api/properties/", include("apps.properties.urls")),
    path("api/rooms/", include("apps.rooms.urls")),
    path("api/guests/", include("apps.guests.urls")),
    path("api/reservations/", include("apps.reservations.urls")),
    path("api/audit/", include("apps.audit.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
