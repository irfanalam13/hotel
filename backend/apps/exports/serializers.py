from rest_framework import serializers
from .models import AccountingExportJob


class AccountingExportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountingExportJob
        fields = "__all__"
        read_only_fields = ["id", "hotel", "status", "file_path", "message", "created_at"]
