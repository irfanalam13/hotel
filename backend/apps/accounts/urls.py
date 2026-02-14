from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.accounts.views import MeView, InviteViewSet, InviteAcceptView, AuthTokenView, AuthRefreshView

router = DefaultRouter()
router.register(r"invites", InviteViewSet, basename="invites")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("invites/accept/", InviteAcceptView.as_view(), name="invite-accept"),

    # JWT
    path("auth/token/", AuthTokenView.as_view(), name="token"),
    path("auth/refresh/", AuthRefreshView.as_view(), name="refresh"),

    path("", include(router.urls)),
]
