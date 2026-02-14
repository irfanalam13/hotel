import uuid
from django.db import models
from apps.properties.models import Property

class Guest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="guests")

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    nationality = models.CharField(max_length=80, blank=True, default="")
    address = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["property", "phone"]), models.Index(fields=["property", "email"])]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

class GuestDocument(models.Model):
    class DocType(models.TextChoices):
        PASSPORT = "passport", "Passport"
        NATIONAL_ID = "national_id", "National ID"
        DRIVING_LICENSE = "driving_license", "Driving License"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="guest_documents")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="documents")

    doc_type = models.CharField(max_length=30, choices=DocType.choices, default=DocType.OTHER)
    doc_number = models.CharField(max_length=80, blank=True, default="")
    issued_country = models.CharField(max_length=80, blank=True, default="")

    file = models.FileField(upload_to="guest_ids/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
