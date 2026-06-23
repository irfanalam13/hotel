from django.contrib import admin

from .models import RatePlan, Room, RoomBlock, RoomType


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "property", "base_rate", "max_adults", "max_children")
    search_fields = ("name", "code")

    def get_queryset(self, request):
        return self.model.all_objects.all()


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("number", "property", "room_type", "status", "is_active")
    list_filter = ("status", "is_active")
    search_fields = ("number",)

    def get_queryset(self, request):
        return self.model.all_objects.all()


@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = ("name", "room_type", "nightly_rate", "is_default", "is_active")

    def get_queryset(self, request):
        return self.model.all_objects.all()


@admin.register(RoomBlock)
class RoomBlockAdmin(admin.ModelAdmin):
    list_display = ("room", "reason", "start_date", "end_date", "is_active")
    list_filter = ("reason", "is_active")

    def get_queryset(self, request):
        return self.model.all_objects.all()
