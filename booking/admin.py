from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Table, Booking, BookingSettings, SpecialDate, TimeSlot

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'capacity', 'location', 'is_active')
    list_filter = ('location', 'is_active', 'capacity')
    search_fields = ('table_number', 'notes')
    list_editable = ('is_active',)

@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Booking Restrictions', {
            'fields': ('min_booking_notice_hours', 'max_booking_days_ahead', 'default_booking_duration_mins',
                      'min_party_size', 'max_party_size')
        }),
        ('Notifications', {
            'fields': ('send_confirmation_emails', 'send_reminder_emails', 'reminder_hours_before')
        }),
        ('Cancellation Policy', {
            'fields': ('allow_online_cancellation', 'cancellation_deadline_hours')
        }),
        ('Deposit Requirements', {
            'fields': ('require_deposit', 'deposit_amount', 'deposit_percentage')
        }),
        ('Automation', {
            'fields': ('auto_confirm_bookings',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow one settings object
        return not BookingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting the settings object
        return False

@admin.register(SpecialDate)
class SpecialDateAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_closed', 'has_special_hours', 'opening_time', 'closing_time')
    list_filter = ('is_closed', 'has_special_hours', 'date')
    search_fields = ('name', 'notes')
    date_hierarchy = 'date'

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('get_day_of_week_display', 'start_time', 'end_time', 'max_bookings', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    list_editable = ('start_time', 'end_time', 'max_bookings', 'is_active')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_total_guests_display', 'date_time', 'status', 'source', 'get_tables_display', 'created_at')
    list_filter = ('status', 'source', 'date_time', 'is_vip', 'preferred_seating_area')
    search_fields = ('name', 'email', 'phone', 'confirmation_code')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'confirmed_at', 'checked_in_at', 'seated_at',
                       'completed_at', 'cancelled_at', 'no_show_at', 'confirmation_code')
    actions = ['mark_as_confirmed', 'mark_as_seated', 'mark_as_completed', 'mark_as_no_show', 'mark_as_cancelled']
    filter_horizontal = ('tables',)

    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'name', 'email', 'phone', 'is_vip', 'vip_notes')
        }),
        ('Guest Count', {
            'fields': ('guest_count_adults', 'guest_count_children', 'guest_count_infants', 'actual_guest_count')
        }),
        ('Reservation Details', {
            'fields': ('date_time', 'duration_minutes', 'end_time', 'time_slot', 'tables', 'preferred_seating_area',
                      'occasion', 'special_request', 'dietary_requirements', 'table_assignment_notes')
        }),
        ('Status and Source', {
            'fields': ('status', 'source', 'confirmation_code', 'assigned_server')
        }),
        ('Deposit Information', {
            'fields': ('deposit_status', 'deposit_amount', 'deposit_transaction_id', 'deposit_paid_at'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('reminder_sent', 'reminder_sent_at', 'feedback_requested', 'feedback_requested_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'checked_in_at', 'seated_at',
                      'completed_at', 'cancelled_at', 'no_show_at'),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason', 'cancellation_by'),
            'classes': ('collapse',)
        }),
    )

    def get_total_guests_display(self, obj):
        return obj.get_total_guests()
    get_total_guests_display.short_description = 'Guests'

    def get_tables_display(self, obj):
        tables = obj.tables.all()
        if not tables:
            return '-'
        return ', '.join([f'Table {t.table_number}' for t in tables])
    get_tables_display.short_description = 'Tables'

    def mark_as_confirmed(self, request, queryset):
        for booking in queryset:
            booking.mark_as_confirmed(by_user=request.user)
        self.message_user(request, f"{queryset.count()} bookings marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected bookings as confirmed"

    def mark_as_seated(self, request, queryset):
        for booking in queryset:
            booking.mark_as_seated(by_user=request.user)
        self.message_user(request, f"{queryset.count()} bookings marked as seated.")
    mark_as_seated.short_description = "Mark selected bookings as seated"

    def mark_as_completed(self, request, queryset):
        for booking in queryset:
            booking.mark_as_completed(by_user=request.user)
        self.message_user(request, f"{queryset.count()} bookings marked as completed.")
    mark_as_completed.short_description = "Mark selected bookings as completed"

    def mark_as_no_show(self, request, queryset):
        for booking in queryset:
            booking.mark_as_no_show(by_user=request.user)
        self.message_user(request, f"{queryset.count()} bookings marked as no-show.")
    mark_as_no_show.short_description = "Mark selected bookings as no-show"

    def mark_as_cancelled(self, request, queryset):
        for booking in queryset:
            booking.mark_as_cancelled(reason='Cancelled by admin', by='staff')
        self.message_user(request, f"{queryset.count()} bookings marked as cancelled.")
    mark_as_cancelled.short_description = "Mark selected bookings as cancelled"
