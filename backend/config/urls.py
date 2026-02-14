from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    
    path("admin/", admin.site.urls),
    
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),


    # public + tenant endpoints
    path("api/tenants/", include("apps.tenants.urls")),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/", include("apps.rooms.urls")),
    path("api/", include("apps.housekeeping.urls")),
    path("api/", include("apps.maintenance.urls")),
    path("api/pos/", include("apps.pos.urls")),

    path("api/properties/", include("apps.properties.urls")),
    path("api/guests/", include("apps.guests.urls")),
    path("api/reservations/", include("apps.reservations.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/dashboards/", include("apps.dashboards.urls")),
    path("api/", include("apps.integrations.urls")),

    path("api/orgs/", include("apps.orgs.urls")),
    path("api/contracts/", include("apps.contracts.urls")),
    path("api/channels/", include("apps.channels.urls")),
    path("api/exports/", include("apps.exports.urls")),
    path("api/support/", include("apps.support.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
