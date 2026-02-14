from rest_framework.routers import DefaultRouter
from .views import AccountingExportJobViewSet

router = DefaultRouter()
router.register("accounting-exports", AccountingExportJobViewSet, basename="accounting-exports")

urlpatterns = router.urls
