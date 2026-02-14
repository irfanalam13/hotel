from django.contrib import admin
from .models import (
    AISettings, KnowledgeBaseFAQ, ReplyTemplate,
    AIRequest, Complaint, Review, AIInsight, AnomalyEvent
)

@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ("tenant", "enabled", "provider", "model", "require_human_approval", "updated_at")
    list_filter = ("enabled", "provider", "require_human_approval")

@admin.register(KnowledgeBaseFAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("tenant", "title", "is_active", "updated_at")
    search_fields = ("title", "question", "answer")

@admin.register(ReplyTemplate)
class ReplyTemplateAdmin(admin.ModelAdmin):
    list_display = ("tenant", "code", "title", "is_active")
    search_fields = ("code", "title", "body")

@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ("tenant", "request_type", "status", "requires_approval", "created_by", "created_at")
    list_filter = ("request_type", "status", "requires_approval")
    search_fields = ("input_text", "redacted_input", "output_text")

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("tenant", "channel", "status", "guest_name", "created_at")
    search_fields = ("guest_name", "message")

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("tenant", "source", "rating", "created_at")
    search_fields = ("text",)

@admin.register(AIInsight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ("tenant", "insight_type", "created_by", "created_at")
    search_fields = ("summary", "suggested_response")

@admin.register(AnomalyEvent)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ("tenant", "event_type", "score", "staff", "status", "created_at")
    list_filter = ("event_type", "status")
