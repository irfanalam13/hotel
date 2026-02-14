from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import GuestViewSet, GuestDocumentViewSet

router = DefaultRouter()
router.register(r"guests", GuestViewSet, basename="guests")
router.register(r"guest-documents", GuestDocumentViewSet, basename="guest-documents")

urlpatterns = [path("", include(router.urls))]
