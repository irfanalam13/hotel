from django.contrib import admin

from .models import Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "organization", "city", "is_active", "is_deleted")
    list_filter = ("is_active", "is_deleted")
    search_fields = ("name", "code", "city")
    autocomplete_fields = ("organization",)

    def get_queryset(self, request):
        # Admin should see every tenant's rows, including soft-deleted.
        return self.model.all_objects.all()
