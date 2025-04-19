from django.contrib import admin
from django.utils import timezone
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
    readonly_fields = ('menu_item', 'quantity', 'price', 'get_total_price', 'get_profit', 'get_profit_margin', 'special_instructions')
    can_delete = False
    fields = ('menu_item', 'quantity', 'price', 'cost_price', 'get_total_price', 'get_profit', 'get_profit_margin', 'special_instructions', 'is_free', 'discount_amount', 'discount_reason', 'is_voided', 'void_reason')

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = 'Total Price'

    def get_profit(self, obj):
        return obj.get_profit()
    get_profit.short_description = 'Profit'

    def get_profit_margin(self, obj):
        return f"{obj.get_profit_margin():.2f}%"
    get_profit_margin.short_description = 'Profit Margin'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'order_type', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'order_type', 'payment_status', 'priority', 'is_gift', 'is_first_order', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email', 'name', 'email', 'phone', 'transaction_id', 'coupon_code')
    readonly_fields = ('order_number', 'user', 'subtotal', 'tax', 'delivery_fee', 'service_fee', 'tip_amount', 'discount_amount', 'total',
                       'created_at', 'updated_at', 'confirmed_at', 'actual_delivery_time', 'payment_date', 'is_first_order')
    inlines = [OrderItemInline]
    actions = ['mark_as_confirmed', 'mark_as_preparing', 'mark_as_ready', 'mark_as_delivered', 'mark_as_completed', 'mark_as_cancelled']

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'order_type', 'priority', 'source')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'transaction_id', 'payment_date')
        }),
        ('Customer Information', {
            'fields': ('name', 'email', 'phone', 'is_first_order')
        }),
        ('Delivery Information', {
            'fields': ('address', 'address_line2', 'city', 'state', 'zip_code', 'country', 'delivery_notes',
                      'tracking_number', 'delivery_provider', 'driver_name', 'driver_phone', 'delivery_distance_km')
        }),
        ('Table Information', {
            'fields': ('table_number', 'number_of_guests'),
            'classes': ('collapse',)
        }),
        ('Gift Information', {
            'fields': ('is_gift', 'gift_message'),
            'classes': ('collapse',)
        }),
        ('Order Details', {
            'fields': ('subtotal', 'tax', 'delivery_fee', 'service_fee', 'tip_amount', 'discount_amount', 'coupon_code', 'total')
        }),
        ('Special Instructions', {
            'fields': ('special_request', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'estimated_delivery_time', 'actual_delivery_time', 'preparation_time_minutes'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('rating', 'feedback'),
            'classes': ('collapse',)
        }),
    )

    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed', confirmed_at=timezone.now())
        self.message_user(request, f"{updated} orders marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected orders as confirmed"

    def mark_as_preparing(self, request, queryset):
        updated = queryset.update(status='preparing')
        self.message_user(request, f"{updated} orders marked as preparing.")
    mark_as_preparing.short_description = "Mark selected orders as preparing"

    def mark_as_ready(self, request, queryset):
        updated = queryset.update(status='ready')
        self.message_user(request, f"{updated} orders marked as ready.")
    mark_as_ready.short_description = "Mark selected orders as ready"

    def mark_as_delivered(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status not in ['delivered', 'completed', 'cancelled']:
                order.mark_as_delivered()
                count += 1
        self.message_user(request, f"{count} orders marked as delivered.")
    mark_as_delivered.short_description = "Mark selected orders as delivered"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} orders marked as completed.")
    mark_as_completed.short_description = "Mark selected orders as completed"

    def mark_as_cancelled(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status not in ['delivered', 'completed', 'cancelled']:
                order.cancel_order("Cancelled by admin")
                count += 1
        self.message_user(request, f"{count} orders cancelled.")
    mark_as_cancelled.short_description = "Mark selected orders as cancelled"
