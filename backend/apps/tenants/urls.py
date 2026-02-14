from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.tenants.views import TenantOnboardView, PlanViewSet, BranchViewSet, SettingsView

router = DefaultRouter()
router.register(r"plans", PlanViewSet, basename="plans")
router.register(r"branches", BranchViewSet, basename="branches")

urlpatterns = [
    path("onboard/", TenantOnboardView.as_view(), name="tenant-onboard"),
    path("settings/", SettingsView.as_view(), name="tenant-settings"),
    path("", include(router.urls)),
]
