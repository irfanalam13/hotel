from django.contrib import admin

from .models import Role, RolePermission


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "is_system")
    list_filter = ("is_system",)
    search_fields = ("code", "name")
    inlines = [RolePermissionInline]
