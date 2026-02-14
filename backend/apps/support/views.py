from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SupportPlan, SupportTicket, TicketMessage
from .serializers import SupportPlanSerializer, SupportTicketSerializer, TicketMessageSerializer
from .services import mark_first_response, close_ticket


class TenantScopedMixin:
    def get_hotel(self):
        return getattr(self.request, "hotel", None) or getattr(self.request, "tenant", None)

    def perform_create(self, serializer):
        serializer.save(hotel=self.get_hotel(), created_by=self.request.user)


class SupportPlanViewSet(ReadOnlyModelViewSet):
    queryset = SupportPlan.objects.filter(is_active=True)
    serializer_class = SupportPlanSerializer
    permission_classes = [IsAuthenticated]


class SupportTicketViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (SupportTicket.objects
                .filter(hotel=self.get_hotel())
                .select_related("plan", "created_by", "assigned_to")
                .prefetch_related("messages")
                .order_by("-created_at"))

    @action(detail=True, methods=["post"])
    def add_message(self, request, pk=None):
        ticket = self.get_object()
        ser = TicketMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        msg = ser.save(ticket=ticket, author=request.user)
        mark_first_response(ticket)
        return Response(TicketMessageSerializer(msg).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        ticket = self.get_object()
        close_ticket(ticket)
        return Response(SupportTicketSerializer(ticket).data)
