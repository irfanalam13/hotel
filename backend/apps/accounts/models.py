from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from apps.common.models import TimeStampedModel
from apps.common.utils import generate_token
from apps.tenants.models import Hotel, Branch

ROLE_CHOICES = [
    ("OWNER", "Owner"),
    ("MANAGER", "Manager"),
    ("RECEPTION", "Reception"),
    ("HOUSEKEEPING", "Housekeeping"),
    ("ACCOUNTANT", "Accountant"),
]

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", "OWNER")
        return self.create_user(email=email, password=password, **extra)

class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # tenant + branch scope
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="users", null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, related_name="users", null=True, blank=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="RECEPTION")

    USERNAME_FIELD = "email"
    objects = UserManager()

    def __str__(self):
        return self.email


class StaffInvite(TimeStampedModel):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="invites")
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="RECEPTION")

    token = models.CharField(max_length=120, unique=True, editable=False)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_invites")

    class Meta:
        unique_together = [("hotel", "email")]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = generate_token(24)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.accepted_at is None and timezone.now() < self.expires_at
