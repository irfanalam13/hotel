from rest_framework.routers import DefaultRouter
from .views import SupportPlanViewSet, SupportTicketViewSet

router = DefaultRouter()
router.register("support-plans", SupportPlanViewSet, basename="support-plans")
router.register("support-tickets", SupportTicketViewSet, basename="support-tickets")

urlpatterns = router.urls
