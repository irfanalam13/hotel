from django.db import models
from django.conf import settings


class HotelGroup(models.Model):
    """
    Enterprise: one company owns multiple hotels (tenants).
    HQ dashboards show consolidated stats.
    """
    name = models.CharField(max_length=200, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_groups")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupHotel(models.Model):
    """
    Links a tenant hotel to a group.
    """
    group = models.ForeignKey(HotelGroup, on_delete=models.CASCADE, related_name="group_hotels")
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="hotel_groups")
    role = models.CharField(max_length=50, default="member")  # HQ, member, etc.

    class Meta:
        unique_together = [("group", "hotel")]

    def __str__(self):
        return f"{self.group} -> {self.hotel}"


class Branch(models.Model):
    """
    Optional if you don't already have Branch.
    If you already have properties.Branch, skip this model and adjust imports.
    """
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="branches")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("hotel", "code")]

    def __str__(self):
        return f"{self.hotel} - {self.code}"
