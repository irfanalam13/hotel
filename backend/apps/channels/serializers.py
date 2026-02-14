from rest_framework import serializers
from .models import ChannelProvider, ChannelCredential, ChannelRoomMap, ChannelSyncJob, ChannelSyncLog


class ChannelProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelProvider
        fields = "__all__"


class ChannelCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelCredential
        fields = "__all__"
        read_only_fields = ["id", "hotel", "created_at"]


class ChannelRoomMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelRoomMap
        fields = "__all__"
        read_only_fields = ["id", "hotel"]


class ChannelSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelSyncLog
        fields = ["id", "level", "event", "payload", "created_at"]


class ChannelSyncJobSerializer(serializers.ModelSerializer):
    logs = ChannelSyncLogSerializer(many=True, read_only=True)

    class Meta:
        model = ChannelSyncJob
        fields = "__all__"
        read_only_fields = ["id", "hotel", "status", "started_at", "finished_at", "created_at"]
