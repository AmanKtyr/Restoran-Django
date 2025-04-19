from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('get_total_price',)

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = 'Total Price'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_total_items', 'get_total_price', 'updated_at')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item', 'quantity', 'price', 'get_total_price', 'special_instructions')
    can_delete = False

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = 'Total Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'order_type', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'order_type', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email', 'full_name', 'email', 'phone')
    readonly_fields = ('order_number', 'user', 'subtotal', 'tax', 'delivery_fee', 'discount', 'total', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'order_type')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Delivery Information', {
            'fields': ('address', 'city', 'state', 'postal_code', 'tracking_number', 'estimated_delivery_time', 'delivered_at')
        }),
        ('Order Details', {
            'fields': ('subtotal', 'tax', 'delivery_fee', 'discount', 'total', 'special_instructions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
