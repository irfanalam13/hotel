from rest_framework import serializers
from .models import CorporateAccount, CorporateContract, Agent, CommissionRule


class CorporateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporateAccount
        fields = "__all__"
        read_only_fields = ["id", "hotel", "created_at"]


class CorporateContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporateContract
        fields = "__all__"
        read_only_fields = ["id", "hotel"]


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = "__all__"
        read_only_fields = ["id", "hotel"]


class CommissionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRule
        fields = "__all__"
        read_only_fields = ["id", "hotel"]
