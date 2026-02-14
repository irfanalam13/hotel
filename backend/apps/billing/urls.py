from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FolioViewSet, InvoiceViewSet, PaymentViewSet,
    RefundRequestViewSet, CashierShiftViewSet, NightAuditViewSet
)

router = DefaultRouter()
router.register(r"folios", FolioViewSet, basename="folios")
router.register(r"invoices", InvoiceViewSet, basename="invoices")
router.register(r"payments", PaymentViewSet, basename="payments")
router.register(r"refunds", RefundRequestViewSet, basename="refunds")
router.register(r"cashier-shifts", CashierShiftViewSet, basename="cashier-shifts")
router.register(r"night-audit", NightAuditViewSet, basename="night-audit")

urlpatterns = [
    path("", include(router.urls)),
]
