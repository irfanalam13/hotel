from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import HotelGroup, GroupHotel
from .serializers import HotelGroupSerializer, GroupHotelSerializer
from .permissions import IsGroupOwner


class HotelGroupViewSet(ModelViewSet):
    serializer_class = HotelGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Owner sees their groups. Later you can add "member" access.
        return HotelGroup.objects.filter(owner=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsGroupOwner()]
        return super().get_permissions()

    @action(detail=True, methods=["get"])
    def hq_summary(self, request, pk=None):
        """
        HQ view: consolidate high-level counts. Real-life useful.
        Expand with occupancy/ADR/RevPAR by joining reports later.
        """
        group = self.get_object()
        hotels = GroupHotel.objects.filter(group=group).select_related("hotel")
        return Response({
            "group_id": group.id,
            "group_name": group.name,
            "hotels": [{"hotel_id": gh.hotel_id, "hotel_name": str(gh.hotel), "role": gh.role} for gh in hotels],
            "note": "Plug this into dashboards: consolidated occupancy/revenue comes from reports app."
        })


class GroupHotelViewSet(ModelViewSet):
    serializer_class = GroupHotelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GroupHotel.objects.filter(group__owner=self.request.user).select_related("group", "hotel")
