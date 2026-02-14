from rest_framework.routers import DefaultRouter
from .views import HotelGroupViewSet, GroupHotelViewSet

router = DefaultRouter()
router.register("groups", HotelGroupViewSet, basename="groups")
router.register("group-hotels", GroupHotelViewSet, basename="group-hotels")

urlpatterns = router.urls
