"""Guest profiles and identity documents (tenant + property scoped)."""
from __future__ import annotations

import builtins

from django.db import models

from apps.common.models import TenantScopedModel


class Guest(TenantScopedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="guests"
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    nationality = models.CharField(max_length=80, blank=True, default="")
    address = models.TextField(blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["organization", "property"]),
            models.Index(fields=["property", "email"]),
            models.Index(fields=["property", "phone"]),
        ]

    def __str__(self) -> str:
        return self.full_name

    @builtins.property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class GuestDocument(TenantScopedModel):
    class DocType(models.TextChoices):
        PASSPORT = "passport", "Passport"
        NATIONAL_ID = "national_id", "National ID"
        DRIVING_LICENSE = "driving_license", "Driving License"
        OTHER = "other", "Other"

    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=30, choices=DocType.choices, default=DocType.OTHER)
    doc_number = models.CharField(max_length=80, blank=True, default="")
    issued_country = models.CharField(max_length=80, blank=True, default="")
    file = models.FileField(upload_to="guest_ids/%Y/%m/", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_doc_type_display()} ({self.doc_number})"
