from rest_framework.routers import DefaultRouter

from .views import GuestViewSet

app_name = "guests"

router = DefaultRouter()
router.register("", GuestViewSet, basename="guest")

urlpatterns = router.urls
