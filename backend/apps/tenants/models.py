from django.db import models
from django.core.validators import MinValueValidator
from apps.common.models import TimeStampedModel

class Plan(TimeStampedModel):
    code = models.CharField(max_length=32, unique=True)   # e.g. STARTER, PRO
    name = models.CharField(max_length=64)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_branches = models.PositiveIntegerField(default=1)
    max_staff = models.PositiveIntegerField(default=5)
    max_rooms = models.PositiveIntegerField(default=20)
    features = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name


class Hotel(TimeStampedModel):
    name = models.CharField(max_length=120)
    hotel_code = models.SlugField(max_length=40, unique=True)  # e.g. everest-inn
    is_active = models.BooleanField(default=True)

    # Optional subdomain support (e.g. everest-inn.yourapp.com)
    subdomain = models.SlugField(max_length=40, unique=True, null=True, blank=True)

    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="hotels")
    timezone = models.CharField(max_length=64, default="Asia/Kathmandu")
    currency = models.CharField(max_length=8, default="NPR")

    def __str__(self):
        return f"{self.name} ({self.hotel_code})"


class Branch(TimeStampedModel):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=40)  # unique per hotel
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("hotel", "code")]

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"


class HotelSettings(TimeStampedModel):
    hotel = models.OneToOneField(Hotel, on_delete=models.CASCADE, related_name="settings")

    # taxes
    vat_percent = models.DecimalField(max_digits=5, decimal_places=2, default=13.00, validators=[MinValueValidator(0)])
    service_charge_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])

    # receipt template (simple)
    receipt_header = models.CharField(max_length=200, default="Thank you for staying with us!")
    receipt_footer = models.CharField(max_length=200, default="Visit again.")

    # policies (real-life: cancellation / check-in)
    policies = models.JSONField(default=dict, blank=True)
    # example:
    # {
    #   "check_in_time": "14:00",
    #   "check_out_time": "12:00",
    #   "cancellation_hours": 24,
    #   "no_show_fee_percent": 50
    # }

    def __str__(self):
        return f"Settings: {self.hotel.name}"
