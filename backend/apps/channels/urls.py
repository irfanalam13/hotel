from rest_framework.routers import DefaultRouter
from .views import ChannelProviderViewSet, ChannelCredentialViewSet, ChannelRoomMapViewSet, ChannelSyncJobViewSet

router = DefaultRouter()
router.register("providers", ChannelProviderViewSet, basename="channel-providers")
router.register("credentials", ChannelCredentialViewSet, basename="channel-credentials")
router.register("room-maps", ChannelRoomMapViewSet, basename="channel-room-maps")
router.register("sync-jobs", ChannelSyncJobViewSet, basename="channel-sync-jobs")

urlpatterns = router.urls
