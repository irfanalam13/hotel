from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PermissionCatalogView, RoleViewSet

app_name = "rbac"

router = DefaultRouter()
router.register("roles", RoleViewSet, basename="role")

urlpatterns = [
    path("permissions/", PermissionCatalogView.as_view(), name="permission-catalog"),
    path("", include(router.urls)),
]
