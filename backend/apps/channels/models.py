from django.db import models


class ChannelProvider(models.Model):
    """
    Example providers: "Beds24", "SiteMinder", "Cloudbeds", etc.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ChannelCredential(models.Model):
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="channel_credentials")
    provider = models.ForeignKey(ChannelProvider, on_delete=models.PROTECT, related_name="credentials")
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    account_id = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("hotel", "provider")]

    def __str__(self):
        return f"{self.hotel} - {self.provider}"


class ChannelRoomMap(models.Model):
    """
    Map your internal room_type/room to provider room_id.
    """
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="channel_room_maps")
    provider = models.ForeignKey(ChannelProvider, on_delete=models.PROTECT, related_name="room_maps")
    room_type = models.ForeignKey("properties.RoomType", on_delete=models.PROTECT, related_name="channel_maps")
    provider_room_id = models.CharField(max_length=120)

    class Meta:
        unique_together = [("hotel", "provider", "room_type")]


class ChannelSyncJob(models.Model):
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="channel_sync_jobs")
    provider = models.ForeignKey(ChannelProvider, on_delete=models.PROTECT, related_name="sync_jobs")
    job_type = models.CharField(max_length=60)  # pull_reservations, push_availability, push_rates
    status = models.CharField(max_length=30, default="queued")  # queued/running/success/failed
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class ChannelSyncLog(models.Model):
    job = models.ForeignKey(ChannelSyncJob, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=20, default="info")  # info/warn/error
    event = models.CharField(max_length=120)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
