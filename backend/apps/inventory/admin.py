from django.contrib import admin
from .models import *

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("tenant","sku","name","unit","reorder_level","expiry_tracking","is_minibar_item","is_active")
    search_fields = ("sku","name")
    list_filter = ("tenant","is_active","expiry_tracking","is_minibar_item")

@admin.register(PurchaseOrder)
class POAdmin(admin.ModelAdmin):
    list_display = ("tenant","po_number","supplier","status","expected_date","created_at")
    list_filter = ("tenant","status")
    search_fields = ("po_number",)

@admin.register(GRN)
class GRNAdmin(admin.ModelAdmin):
    list_display = ("tenant","grn_number","po","location","received_date","created_at")
    list_filter = ("tenant","received_date")

@admin.register(StockMovement)
class StockMoveAdmin(admin.ModelAdmin):
    list_display = ("tenant","movement_type","item","location","qty","reference","created_at")
    list_filter = ("tenant","movement_type","location")
    search_fields = ("reference","item__name","item__sku")
