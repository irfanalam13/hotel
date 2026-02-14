from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import CorporateAccount, CorporateContract, Agent, CommissionRule
from .serializers import (
    CorporateAccountSerializer, CorporateContractSerializer,
    AgentSerializer, CommissionRuleSerializer
)


class TenantScopedMixin:
    def get_hotel(self):
        # adapt to your tenant middleware (subdomain/hotel-code)
        # common pattern: request.tenant or request.hotel
        return getattr(self.request, "hotel", None) or getattr(self.request, "tenant", None)

    def perform_create(self, serializer):
        serializer.save(hotel=self.get_hotel())


class CorporateAccountViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = CorporateAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CorporateAccount.objects.filter(hotel=self.get_hotel(), is_active=True)


class CorporateContractViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = CorporateContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CorporateContract.objects.filter(hotel=self.get_hotel(), is_active=True).select_related("corporate")


class AgentViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Agent.objects.filter(hotel=self.get_hotel(), is_active=True)


class CommissionRuleViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = CommissionRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CommissionRule.objects.filter(hotel=self.get_hotel(), is_active=True).select_related("agent")
