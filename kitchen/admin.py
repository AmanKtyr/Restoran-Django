from django.contrib import admin
from .models import (
    KitchenStation, KitchenDisplay, MenuItemStation,
    OrderItemStatus, KitchenLog, KitchenAlert
)

@admin.register(KitchenStation)
class KitchenStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('display_order', 'name')

@admin.register(KitchenDisplay)
class KitchenDisplayAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'get_stations')
    list_filter = ('is_active', 'stations')
    search_fields = ('name', 'description')
    filter_horizontal = ('stations',)

    def get_stations(self, obj):
        return ", ".join([station.name for station in obj.stations.all()])
    get_stations.short_description = 'Stations'

@admin.register(MenuItemStation)
class MenuItemStationAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'station', 'preparation_time_minutes')
    list_filter = ('station',)
    search_fields = ('menu_item__name', 'station__name')
    autocomplete_fields = ('menu_item',)

@admin.register(OrderItemStatus)
class OrderItemStatusAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'status', 'station', 'assigned_to', 'started_at', 'completed_at')
    list_filter = ('status', 'station', 'assigned_to')
    search_fields = ('order_item__menu_item__name', 'notes')
    readonly_fields = ('started_at', 'completed_at', 'estimated_completion_time')
    raw_id_fields = ('order_item',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order_item__menu_item', 'station', 'assigned_to'
        )

@admin.register(KitchenLog)
class KitchenLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'order', 'order_item', 'event_type', 'user', 'station')
    list_filter = ('event_type', 'timestamp', 'station')
    search_fields = ('order__order_number', 'event_description')
    readonly_fields = ('timestamp',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order', 'order_item__menu_item', 'station', 'user'
        )

@admin.register(KitchenAlert)
class KitchenAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'created_by', 'created_at', 'expires_at', 'is_active', 'is_expired')
    list_filter = ('priority', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    filter_horizontal = ('stations',)

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
