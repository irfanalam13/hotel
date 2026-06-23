from django.contrib import admin

from .models import (
    Reservation,
    ReservationCharge,
    ReservationGuest,
    ReservationRoom,
    ReservationStatusLog,
)


class ReservationRoomInline(admin.TabularInline):
    model = ReservationRoom
    extra = 0
    raw_id_fields = ("room", "room_type")


class ReservationChargeInline(admin.TabularInline):
    model = ReservationCharge
    extra = 0


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("code", "property", "status", "check_in", "check_out", "total_amount")
    list_filter = ("status",)
    search_fields = ("code",)
    inlines = [ReservationRoomInline, ReservationChargeInline]

    def get_queryset(self, request):
        return self.model.all_objects.all()


@admin.register(ReservationStatusLog)
class ReservationStatusLogAdmin(admin.ModelAdmin):
    list_display = ("reservation", "from_status", "to_status", "by_user", "created_at")
    list_filter = ("to_status",)


admin.site.register(ReservationGuest)
