from rest_framework import serializers
from .models import (
    AISettings, KnowledgeBaseFAQ, ReplyTemplate,
    AIRequest, Complaint, Review, AIInsight, AnomalyEvent
)

class AISettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISettings
        fields = "__all__"
        read_only_fields = ("tenant", "updated_at")

class KnowledgeBaseFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBaseFAQ
        fields = "__all__"
        read_only_fields = ("tenant", "updated_at")

class ReplyTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplyTemplate
        fields = "__all__"
        read_only_fields = ("tenant",)

class AIRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRequest
        fields = "__all__"
        read_only_fields = (
            "tenant", "created_by", "redacted_input",
            "output_text", "confidence", "sources",
            "approved_by", "approved_at",
            "status", "error_message", "created_at"
        )

class AIApproveSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = "__all__"
        read_only_fields = ("tenant", "created_at")

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ("tenant", "created_at")

class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = "__all__"
        read_only_fields = ("tenant", "created_by", "created_at")

class AnomalyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyEvent
        fields = "__all__"
        read_only_fields = ("tenant", "created_at")
