from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ReservationViewSet, AvailabilityViewSet

router = DefaultRouter()
router.register(r"reservations", ReservationViewSet, basename="reservations")
router.register(r"availability", AvailabilityViewSet, basename="availability")

urlpatterns = [path("", include(router.urls))]
