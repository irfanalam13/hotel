from rest_framework.routers import DefaultRouter
from .views import CleaningTaskViewSet

router = DefaultRouter()
router.register(r"housekeeping/tasks", CleaningTaskViewSet, basename="housekeeping-tasks")

urlpatterns = router.urls
