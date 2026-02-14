from django.contrib import admin
from .models import (
    MenuCategory, MenuItem, DiningTable,
    POSOrder, POSOrderItem,
    KOTTicket, KOTLine,
    CashDrawerShift, Settlement,
    ApprovalRequest, RoomPost
)

class POSOrderItemInline(admin.TabularInline):
    model = POSOrderItem
    extra = 0

@admin.register(POSOrder)
class POSOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "branch", "status", "source", "table", "total", "created_at")
    list_filter = ("status", "source", "branch")
    search_fields = ("id", "waiter_name", "notes")
    inlines = [POSOrderItemInline]

admin.site.register(MenuCategory)
admin.site.register(MenuItem)
admin.site.register(DiningTable)
admin.site.register(KOTTicket)
admin.site.register(KOTLine)
admin.site.register(CashDrawerShift)
admin.site.register(Settlement)
admin.site.register(ApprovalRequest)
admin.site.register(RoomPost)
