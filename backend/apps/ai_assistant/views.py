from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    AISettings, KnowledgeBaseFAQ, ReplyTemplate, AIRequest,
    Complaint, Review, AIInsight, AnomalyEvent
)
from .serializers import (
    AISettingsSerializer, KnowledgeBaseFAQSerializer, ReplyTemplateSerializer,
    AIRequestSerializer, AIApproveSerializer,
    ComplaintSerializer, ReviewSerializer, AIInsightSerializer, AnomalyEventSerializer
)
from .permissions import IsTenantStaff, IsManagerOrAdmin
from .services.redact import redact_pii
from .services.prompts import (
    system_policy_prompt, reply_prompt, summarize_complaint_prompt, summarize_review_prompt
)
from .services.provider import get_provider


def _tenant(request):
    # Your middleware should set request.tenant
    return getattr(request, "tenant", None)


def _get_settings_or_default(tenant):
    s = AISettings.objects.filter(tenant=tenant).order_by("-updated_at").first()
    if not s:
        s = AISettings.objects.create(tenant=tenant, enabled=False, provider="dummy", model="")
    return s


def _build_context(tenant, user_message: str, limit=8):
    """
    Practical retrieval: simple tag/title/question match.
    Later you can replace with embeddings/vector db.
    """
    qs = KnowledgeBaseFAQ.objects.filter(tenant=tenant, is_active=True)
    msg = (user_message or "").lower()
    # naive match
    qs = qs.filter(Q(title__icontains=msg) | Q(question__icontains=msg) | Q(answer__icontains=msg))[:limit]
    parts = []
    sources = []
    for faq in qs:
        parts.append(f"[FAQ:{faq.id}] Q: {faq.question}\nA: {faq.answer}\n")
        sources.append(f"FAQ:{faq.id}")
    return "\n".join(parts), sources


class AISettingsViewSet(viewsets.ModelViewSet):
    serializer_class = AISettingsSerializer
    permission_classes = [IsManagerOrAdmin]

    def get_queryset(self):
        return AISettings.objects.filter(tenant=_tenant(self.request))

    def perform_create(self, serializer):
        serializer.save(tenant=_tenant(self.request))


class KnowledgeBaseFAQViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgeBaseFAQSerializer
    permission_classes = [IsManagerOrAdmin]

    def get_queryset(self):
        return KnowledgeBaseFAQ.objects.filter(tenant=_tenant(self.request))

    def perform_create(self, serializer):
        serializer.save(tenant=_tenant(self.request))


class ReplyTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = ReplyTemplateSerializer
    permission_classes = [IsManagerOrAdmin]

    def get_queryset(self):
        return ReplyTemplate.objects.filter(tenant=_tenant(self.request))

    def perform_create(self, serializer):
        serializer.save(tenant=_tenant(self.request))


class AIRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIRequestSerializer
    permission_classes = [IsTenantStaff]

    def get_queryset(self):
        return AIRequest.objects.filter(tenant=_tenant(self.request)).order_by("-created_at")

    @action(detail=False, methods=["post"], permission_classes=[IsTenantStaff])
    def reply_assistant(self, request):
        tenant = _tenant(request)
        settings_obj = _get_settings_or_default(tenant)

        if not settings_obj.enabled:
            return Response({"detail": "AI is disabled for this tenant."}, status=status.HTTP_400_BAD_REQUEST)

        user_text = request.data.get("message", "") or ""
        if not user_text.strip():
            return Response({"detail": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        redacted = redact_pii(user_text) if settings_obj.redact_pii else user_text

        # blocklist quick safety
        lowered = redacted.lower()
        if any(p.lower() in lowered for p in (settings_obj.block_phrases or [])):
            ai_req = AIRequest.objects.create(
                tenant=tenant,
                request_type=AIRequest.TYPE_REPLY,
                created_by=request.user,
                input_text=user_text,
                redacted_input=redacted,
                status="blocked",
                requires_approval=True,
                error_message="Blocked by tenant safety rules.",
            )
            return Response({"request_id": ai_req.id, "status": "blocked"}, status=status.HTTP_403_FORBIDDEN)

        context, sources = _build_context(tenant, redacted)
        system = system_policy_prompt()
        prompt = reply_prompt(redacted, context)

        provider = get_provider(settings_obj.provider, settings_obj.model)
        ai_req = AIRequest.objects.create(
            tenant=tenant,
            request_type=AIRequest.TYPE_REPLY,
            created_by=request.user,
            input_text=user_text,
            redacted_input=redacted,
            requires_approval=settings_obj.require_human_approval,
            status="pending" if settings_obj.require_human_approval else "completed",
        )

        try:
            result = provider.generate(system=system, prompt=prompt, max_tokens=settings_obj.max_tokens)
            ai_req.output_text = result.text or ""
            ai_req.confidence = float(result.confidence or 0.0)
            ai_req.sources = list(set((result.sources or []) + sources))
            if not settings_obj.require_human_approval:
                ai_req.status = "completed"
            ai_req.save(update_fields=["output_text", "confidence", "sources", "status"])
        except Exception as e:
            ai_req.status = "failed"
            ai_req.error_message = str(e)
            ai_req.save(update_fields=["status", "error_message"])
            return Response({"request_id": ai_req.id, "status": "failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "request_id": ai_req.id,
            "requires_approval": ai_req.requires_approval,
            "status": ai_req.status,
            "output": ai_req.output_text,
            "confidence": ai_req.confidence,
            "sources": ai_req.sources,
        })

    @action(detail=False, methods=["post"], permission_classes=[IsManagerOrAdmin])
    def approve(self, request):
        ser = AIApproveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        tenant = _tenant(request)
        rid = ser.validated_data["request_id"]
        ai_req = AIRequest.objects.filter(tenant=tenant, id=rid).first()
        if not ai_req:
            return Response({"detail": "Not found"}, status=404)

        if ai_req.status != "pending":
            return Response({"detail": f"Cannot approve status={ai_req.status}"}, status=400)

        ai_req.approve(request.user)
        return Response({"detail": "Approved", "request_id": ai_req.id})


class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [IsTenantStaff]

    def get_queryset(self):
        return Complaint.objects.filter(tenant=_tenant(self.request)).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(tenant=_tenant(self.request))

    @action(detail=True, methods=["post"], permission_classes=[IsTenantStaff])
    def summarize(self, request, pk=None):
        tenant = _tenant(request)
        complaint = self.get_object()
        settings_obj = _get_settings_or_default(tenant)
        if not settings_obj.enabled:
            return Response({"detail": "AI is disabled for this tenant."}, status=400)

        text = complaint.message
        redacted = redact_pii(text) if settings_obj.redact_pii else text

        provider = get_provider(settings_obj.provider, settings_obj.model)
        system = system_policy_prompt()
        prompt = summarize_complaint_prompt(redacted)

        ai_req = AIRequest.objects.create(
            tenant=tenant,
            request_type=AIRequest.TYPE_COMPLAINT,
            created_by=request.user,
            input_text=text,
            redacted_input=redacted,
            requires_approval=True,
            status="completed",
        )

        try:
            result = provider.generate(system=system, prompt=prompt, max_tokens=settings_obj.max_tokens)
            ai_req.output_text = result.text or ""
            ai_req.save(update_fields=["output_text"])
        except Exception as e:
            ai_req.status = "failed"
            ai_req.error_message = str(e)
            ai_req.save(update_fields=["status", "error_message"])
            return Response({"detail": "AI failed", "request_id": ai_req.id}, status=500)

        # Minimal parsing (keep robust: store full text too)
        out = ai_req.output_text
        summary = out
        tags = []
        risk_flags = []

        insight = AIInsight.objects.create(
            tenant=tenant,
            insight_type=AIInsight.TYPE_COMPLAINT,
            complaint=complaint,
            summary=summary,
            suggested_response="",
            tags=tags,
            risk_flags=risk_flags,
            created_by=request.user,
        )
        return Response({"insight_id": insight.id, "ai_request_id": ai_req.id, "raw": out})


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsTenantStaff]

    def get_queryset(self):
        return Review.objects.filter(tenant=_tenant(self.request)).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(tenant=_tenant(self.request))

    @action(detail=True, methods=["post"], permission_classes=[IsTenantStaff])
    def summarize(self, request, pk=None):
        tenant = _tenant(request)
        review = self.get_object()
        settings_obj = _get_settings_or_default(tenant)
        if not settings_obj.enabled:
            return Response({"detail": "AI is disabled for this tenant."}, status=400)

        redacted = redact_pii(review.text) if settings_obj.redact_pii else review.text
        provider = get_provider(settings_obj.provider, settings_obj.model)
        system = system_policy_prompt()
        prompt = summarize_review_prompt(redacted, rating=review.rating)

        ai_req = AIRequest.objects.create(
            tenant=tenant,
            request_type=AIRequest.TYPE_REVIEW,
            created_by=request.user,
            input_text=review.text,
            redacted_input=redacted,
            requires_approval=False,
            status="completed",
        )

        try:
            result = provider.generate(system=system, prompt=prompt, max_tokens=settings_obj.max_tokens)
            ai_req.output_text = result.text or ""
            ai_req.save(update_fields=["output_text"])
        except Exception as e:
            ai_req.status = "failed"
            ai_req.error_message = str(e)
            ai_req.save(update_fields=["status", "error_message"])
            return Response({"detail": "AI failed", "request_id": ai_req.id}, status=500)

        insight = AIInsight.objects.create(
            tenant=tenant,
            insight_type=AIInsight.TYPE_REVIEW,
            review=review,
            summary=ai_req.output_text,
            suggested_response="",
            tags=[],
            risk_flags=[],
            created_by=request.user,
        )
        return Response({"insight_id": insight.id, "ai_request_id": ai_req.id, "raw": ai_req.output_text})


class AIInsightViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIInsightSerializer
    permission_classes = [IsTenantStaff]

    def get_queryset(self):
        return AIInsight.objects.filter(tenant=_tenant(self.request)).order_by("-created_at")


class AnomalyEventViewSet(viewsets.ModelViewSet):
    serializer_class = AnomalyEventSerializer
    permission_classes = [IsManagerOrAdmin]

    def get_queryset(self):
        return AnomalyEvent.objects.filter(tenant=_tenant(self.request)).order_by("-created_at")

    @action(detail=True, methods=["post"], permission_classes=[IsManagerOrAdmin])
    def acknowledge(self, request, pk=None):
        ev = self.get_object()
        ev.status = "ack"
        ev.save(update_fields=["status"])
        return Response({"detail": "Acknowledged"})
