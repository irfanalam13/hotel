from rest_framework.routers import DefaultRouter
from .views import CorporateAccountViewSet, CorporateContractViewSet, AgentViewSet, CommissionRuleViewSet

router = DefaultRouter()
router.register("corporates", CorporateAccountViewSet, basename="corporates")
router.register("contracts", CorporateContractViewSet, basename="contracts")
router.register("agents", AgentViewSet, basename="agents")
router.register("commissions", CommissionRuleViewSet, basename="commissions")

urlpatterns = router.urls
