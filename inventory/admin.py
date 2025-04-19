from django.contrib import admin
from .models import (
    Supplier, Category, Unit, InventoryItem, SupplierItem,
    StockAdjustment, PurchaseOrder, PurchaseOrderItem,
    InventoryCheck, InventoryCheckItem
)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person', 'email', 'phone')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')

class SupplierItemInline(admin.TabularInline):
    model = SupplierItem
    extra = 1

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'current_stock', 'unit', 'minimum_stock', 'cost_per_unit', 'stock_status', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    inlines = [SupplierItemInline]
    readonly_fields = ('stock_status', 'needs_reordering', 'total_value')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'category', 'unit', 'is_active')
        }),
        ('Stock Information', {
            'fields': ('current_stock', 'minimum_stock', 'optimal_stock', 'cost_per_unit', 'expiry_date', 'storage_location')
        }),
        ('Status', {
            'fields': ('stock_status', 'needs_reordering', 'total_value')
        }),
    )

@admin.register(SupplierItem)
class SupplierItemAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'item', 'supplier_price', 'is_preferred_supplier', 'last_ordered_date')
    list_filter = ('supplier', 'is_preferred_supplier')
    search_fields = ('supplier__name', 'item__name')

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('item', 'adjustment_type', 'quantity', 'date', 'performed_by')
    list_filter = ('adjustment_type', 'date')
    search_fields = ('item__name', 'reason', 'reference_number')
    readonly_fields = ('date',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item', 'performed_by')

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'status', 'created_at', 'expected_delivery_date', 'total_amount')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'supplier__name')
    readonly_fields = ('created_at', 'updated_at', 'total_amount')
    inlines = [PurchaseOrderItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('supplier', 'created_by', 'approved_by')

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'item', 'quantity', 'unit_price', 'received_quantity', 'subtotal', 'is_fully_received')
    list_filter = ('purchase_order__status',)
    search_fields = ('purchase_order__order_number', 'item__name')
    readonly_fields = ('subtotal', 'is_fully_received')

class InventoryCheckItemInline(admin.TabularInline):
    model = InventoryCheckItem
    extra = 1

@admin.register(InventoryCheck)
class InventoryCheckAdmin(admin.ModelAdmin):
    list_display = ('check_date', 'status', 'performed_by', 'created_at', 'completed_at')
    list_filter = ('status', 'check_date')
    search_fields = ('notes',)
    readonly_fields = ('created_at', 'completed_at')
    inlines = [InventoryCheckItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('performed_by')

@admin.register(InventoryCheckItem)
class InventoryCheckItemAdmin(admin.ModelAdmin):
    list_display = ('inventory_check', 'item', 'expected_quantity', 'actual_quantity', 'discrepancy', 'discrepancy_percentage')
    list_filter = ('inventory_check__status',)
    search_fields = ('item__name', 'notes')
    readonly_fields = ('discrepancy', 'discrepancy_percentage')
