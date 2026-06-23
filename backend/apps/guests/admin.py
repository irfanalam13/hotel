from django.contrib import admin

from .models import Guest, GuestDocument


class GuestDocumentInline(admin.TabularInline):
    model = GuestDocument
    extra = 0


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "property", "email", "phone")
    search_fields = ("first_name", "last_name", "email", "phone")
    inlines = [GuestDocumentInline]

    def get_queryset(self, request):
        return self.model.all_objects.all()
