from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuCategoryViewSet, MenuItemViewSet, DiningTableViewSet,
    POSOrderViewSet, SettlementViewSet,
    RoomPostViewSet, CashDrawerShiftViewSet,
    ApprovalRequestViewSet
)

router = DefaultRouter()
router.register(r"menu/categories", MenuCategoryViewSet, basename="pos-menu-categories")   # /pos/menu/categories/
router.register(r"menu/items", MenuItemViewSet, basename="pos-menu-items")               # /pos/menu/items/
router.register(r"tables", DiningTableViewSet, basename="pos-tables")                    # /pos/tables/
router.register(r"orders", POSOrderViewSet, basename="pos-orders")                       # /pos/orders/
router.register(r"settlements", SettlementViewSet, basename="pos-settlements")           # /pos/settlements/
router.register(r"cash-shifts", CashDrawerShiftViewSet, basename="pos-cash-shifts")      # /pos/cash-shifts/
router.register(r"approvals", ApprovalRequestViewSet, basename="pos-approvals")          # /pos/approvals/

urlpatterns = [
    path("", include(router.urls)),
    path("", include(RoomPostViewSet().get_urls()) if hasattr(RoomPostViewSet, "get_urls") else include([])),
]
