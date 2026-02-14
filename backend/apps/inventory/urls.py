from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    UnitViewSet, ItemCategoryViewSet, InventoryLocationViewSet,
    ItemViewSet, SupplierViewSet,
    PurchaseOrderViewSet, GRNViewSet,
    StockMovementViewSet, StockIssueViewSet, StockCountViewSet,
    MinibarTemplateViewSet, RoomMinibarViewSet, MinibarCountViewSet
)

router = DefaultRouter()
router.register(r"inventory/units", UnitViewSet, basename="inv-units")
router.register(r"inventory/categories", ItemCategoryViewSet, basename="inv-categories")
router.register(r"inventory/locations", InventoryLocationViewSet, basename="inv-locations")
router.register(r"inventory/items", ItemViewSet, basename="inv-items")
router.register(r"inventory/suppliers", SupplierViewSet, basename="inv-suppliers")

router.register(r"purchase/orders", PurchaseOrderViewSet, basename="purchase-orders")
router.register(r"purchase/grns", GRNViewSet, basename="purchase-grns")

router.register(r"stock/movements", StockMovementViewSet, basename="stock-movements")
router.register(r"stock/issues", StockIssueViewSet, basename="stock-issues")
router.register(r"stock/counts", StockCountViewSet, basename="stock-counts")

router.register(r"minibar/templates", MinibarTemplateViewSet, basename="minibar-templates")
router.register(r"minibar/rooms", RoomMinibarViewSet, basename="minibar-rooms")
router.register(r"minibar/counts", MinibarCountViewSet, basename="minibar-counts")

urlpatterns = [
    path("", include(router.urls)),
]
