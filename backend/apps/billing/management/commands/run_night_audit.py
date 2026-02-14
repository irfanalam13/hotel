from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.tenants.models import Hotel
from apps.billing.services import run_night_audit

class Command(BaseCommand):
    help = "Run night audit for a hotel (locks the business date)"

    def add_arguments(self, parser):
        parser.add_argument("hotel_id", type=int)
        parser.add_argument("--date", type=str, default=str(timezone.localdate()))

    def handle(self, *args, **opts):
        hotel = Hotel.objects.get(id=opts["hotel_id"])
        audit = run_night_audit(hotel=hotel, business_date=opts["date"], ran_by=None)
        self.stdout.write(self.style.SUCCESS(f"Night audit done: {audit.hotel} {audit.business_date}"))
