from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from .models import IntegrationConfig, MessageTemplate, OutboundMessage, PaymentIntent, IntegrationKind
from .serializers import (
    IntegrationConfigSerializer, MessageTemplateSerializer, OutboundMessageSerializer, PaymentIntentSerializer
)
from .services import queue_message, render_from_template
from .tasks import send_message_task
from .payments import create_payment_intent
from .booking_widget import create_widget_booking
from .ota_import import import_ota_csv


class TenantScopedMixin:
    """
    Replace tenant_id extraction with YOUR multi-tenant method:
    - subdomain middleware
    - request.tenant
    - request.user.tenant_id
    """
    def get_tenant_id(self):
        # safest default for now:
        return getattr(self.request, "tenant_id", None) or getattr(self.request.user, "tenant_id", None)


class IntegrationConfigViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    serializer_class = IntegrationConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IntegrationConfig.objects.filter(tenant_id=self.get_tenant_id()).order_by("kind")

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.get_tenant_id())


class MessageTemplateViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    serializer_class = MessageTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MessageTemplate.objects.filter(tenant_id=self.get_tenant_id()).order_by("kind", "code")

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.get_tenant_id())


class OutboundMessageViewSet(TenantScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = OutboundMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OutboundMessage.objects.filter(tenant_id=self.get_tenant_id()).order_by("-created_at")

    @action(detail=False, methods=["post"])
    def send(self, request):
        """
        Send ad-hoc message (front desk manually sends to guest).
        Body:
        { kind: "sms|whatsapp|email", to: "...", subject?: "", body: "", metadata?: {} }
        """
        tenant_id = self.get_tenant_id()
        kind = request.data["kind"]
        msg = queue_message(
            tenant_id=tenant_id,
            kind=kind,
            to=request.data["to"],
            subject=request.data.get("subject", ""),
            body=request.data.get("body", ""),
            created_by=request.user,
            metadata=request.data.get("metadata", {}),
        )
        send_message_task.delay(str(msg.id))
        return Response({"id": str(msg.id), "status": msg.status})


class AutomationViewSet(TenantScopedMixin, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def send_booking_confirmation(self, request):
        """
        Real-life: after reservation booked, auto-send WhatsApp/SMS/Email using templates.
        Body:
        {
          "reservation_id": "...",
          "channel": "email|sms|whatsapp",
          "to": "...",
          "template_code": "BOOKING_CONFIRM",
          "ctx": { "guest_name": "...", "checkin": "2026-01-30", ... }
        }
        """
        tenant_id = self.get_tenant_id()
        channel = request.data["channel"]
        code = request.data["template_code"]
        ctx = request.data.get("ctx", {})

        tpl, subject, body = render_from_template(tenant_id=tenant_id, kind=channel, code=code, ctx=ctx)
        msg = queue_message(
            tenant_id=tenant_id,
            kind=channel,
            to=request.data["to"],
            subject=subject,
            body=body,
            created_by=request.user,
            metadata={
                "reservation_id": request.data.get("reservation_id"),
                "wa_template_name": getattr(tpl, "wa_template_name", ""),
                "template_code": code,
            },
        )
        send_message_task.delay(str(msg.id))
        return Response({"queued_message_id": str(msg.id)})


class PaymentIntentViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    serializer_class = PaymentIntentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentIntent.objects.filter(tenant_id=self.get_tenant_id()).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        tenant_id = self.get_tenant_id()
        intent = create_payment_intent(
            tenant_id=tenant_id,
            amount=request.data["amount"],
            currency=request.data.get("currency", "NPR"),
            reference_type=request.data.get("reference_type", "reservation"),
            reference_id=request.data["reference_id"],
        )
        return Response(PaymentIntentSerializer(intent).data)


class PublicBookingWidgetViewSet(TenantScopedMixin, viewsets.ViewSet):
    """
    Public endpoint for website widget.
    You must protect with:
    - widget_api_key per tenant, OR
    - allowed domain list, OR
    - signed token
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def create_booking(self, request):
        tenant_id = request.data.get("tenant_id")  # or derive from subdomain
        res = create_widget_booking(tenant_id=tenant_id, payload=request.data)
        return Response({"reservation_id": str(res.id), "status": res.status})


class OTAImportViewSet(TenantScopedMixin, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @action(detail=False, methods=["post"])
    def csv(self, request):
        tenant_id = self.get_tenant_id()
        f = request.FILES["file"]
        result = import_ota_csv(tenant_id=tenant_id, file_obj=f, source_name=request.data.get("source", "OTA_CSV"))
        return Response(result)
