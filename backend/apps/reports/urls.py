from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    KPIView, RevenueByDepartmentView, CxlNoShowView,
    DiscountRefundAuditView, StockVarianceView, StaffActivityView,
    ExportJobViewSet, ExportScheduleViewSet
)

router = DefaultRouter()
router.register(r"exports", ExportJobViewSet, basename="exports")
router.register(r"schedules", ExportScheduleViewSet, basename="schedules")

urlpatterns = [
    path("kpi/", KPIView.as_view()),
    path("revenue-by-department/", RevenueByDepartmentView.as_view()),
    path("cancellations/", CxlNoShowView.as_view()),
    path("discount-refund-audit/", DiscountRefundAuditView.as_view()),
    path("stock-variance/", StockVarianceView.as_view()),
    path("staff-activity/", StaffActivityView.as_view()),
    path("", include(router.urls)),
]
