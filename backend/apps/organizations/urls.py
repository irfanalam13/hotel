from rest_framework.routers import SimpleRouter

from .views import MembershipViewSet, OrganizationViewSet

app_name = "organizations"

# SimpleRouter (no API-root view) so the organization list at the empty prefix
# is not shadowed. Members are registered first so "members/" matches as a
# literal prefix rather than being captured as an organization id.
members_router = SimpleRouter()
members_router.register("members", MembershipViewSet, basename="member")

orgs_router = SimpleRouter()
orgs_router.register("", OrganizationViewSet, basename="organization")

urlpatterns = members_router.urls + orgs_router.urls
