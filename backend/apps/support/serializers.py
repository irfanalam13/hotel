from rest_framework import serializers
from .models import SupportPlan, SupportTicket, TicketMessage


class SupportPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportPlan
        fields = "__all__"


class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = "__all__"
        read_only_fields = ["id", "author", "created_at"]


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ["id", "hotel", "created_by", "created_at", "first_response_at", "resolved_at"]
