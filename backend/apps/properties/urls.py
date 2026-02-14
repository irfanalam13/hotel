from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, AmenityViewSet, RoomTypeViewSet, RoomViewSet

router = DefaultRouter()
router.register(r"list", PropertyViewSet, basename="properties")
router.register(r"amenities", AmenityViewSet, basename="amenities")
router.register(r"room-types", RoomTypeViewSet, basename="room-types")
router.register(r"rooms", RoomViewSet, basename="rooms")

urlpatterns = [path("", include(router.urls))]
