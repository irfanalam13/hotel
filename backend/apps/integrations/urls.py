from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IntegrationConfigViewSet,
    MessageTemplateViewSet,
    OutboundMessageViewSet,
    AutomationViewSet,
    PaymentIntentViewSet,
    PublicBookingWidgetViewSet,
    OTAImportViewSet,
)

router = DefaultRouter()
router.register(r"integrations/configs", IntegrationConfigViewSet, basename="integration-configs")
router.register(r"integrations/templates", MessageTemplateViewSet, basename="integration-templates")
router.register(r"integrations/messages", OutboundMessageViewSet, basename="integration-messages")
router.register(r"integrations/automation", AutomationViewSet, basename="integration-automation")
router.register(r"integrations/payments", PaymentIntentViewSet, basename="integration-payments")
router.register(r"public/widget", PublicBookingWidgetViewSet, basename="public-booking-widget")
router.register(r"integrations/ota-import", OTAImportViewSet, basename="ota-import")

urlpatterns = [
    path("", include(router.urls)),
]
