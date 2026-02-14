from rest_framework.routers import DefaultRouter
from .views import (
    AISettingsViewSet, KnowledgeBaseFAQViewSet, ReplyTemplateViewSet,
    AIRequestViewSet, ComplaintViewSet, ReviewViewSet, AIInsightViewSet, AnomalyEventViewSet
)

router = DefaultRouter()
router.register(r"ai/settings", AISettingsViewSet, basename="ai-settings")
router.register(r"ai/faqs", KnowledgeBaseFAQViewSet, basename="ai-faqs")
router.register(r"ai/templates", ReplyTemplateViewSet, basename="ai-templates")
router.register(r"ai/requests", AIRequestViewSet, basename="ai-requests")
router.register(r"ai/complaints", ComplaintViewSet, basename="ai-complaints")
router.register(r"ai/reviews", ReviewViewSet, basename="ai-reviews")
router.register(r"ai/insights", AIInsightViewSet, basename="ai-insights")
router.register(r"ai/anomalies", AnomalyEventViewSet, basename="ai-anomalies")

urlpatterns = router.urls
