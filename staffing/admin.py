from django.contrib import admin
from .models import (
    Department, Position, StaffProfile, Skill, StaffSkill,
    Availability, TimeOffRequest, Shift, ShiftSwapRequest,
    ShiftTemplate, Schedule, ClockInOut, PayrollPeriod, PayrollRecord
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'hourly_rate', 'is_full_time', 'is_active')
    list_filter = ('department', 'is_full_time', 'is_active')
    search_fields = ('title', 'description')

class StaffSkillInline(admin.TabularInline):
    model = StaffSkill
    extra = 1

class AvailabilityInline(admin.TabularInline):
    model = Availability
    extra = 1

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'employment_status', 'hire_date', 'hourly_rate', 'is_active')
    list_filter = ('position__department', 'employment_status', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    inlines = [StaffSkillInline, AvailabilityInline]
    fieldsets = (
        (None, {
            'fields': ('user', 'position', 'employment_status', 'is_active')
        }),
        ('Employment Details', {
            'fields': ('hire_date', 'hourly_rate', 'max_hours_per_week')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(StaffSkill)
class StaffSkillAdmin(admin.ModelAdmin):
    list_display = ('staff', 'skill', 'proficiency', 'certified', 'certification_date')
    list_filter = ('skill', 'proficiency', 'certified')
    search_fields = ('staff__user__username', 'skill__name')

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('staff', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available')
    search_fields = ('staff__user__username',)

@admin.register(TimeOffRequest)
class TimeOffRequestAdmin(admin.ModelAdmin):
    list_display = ('staff', 'start_date', 'end_date', 'request_type', 'status', 'submitted_at')
    list_filter = ('request_type', 'status', 'start_date')
    search_fields = ('staff__user__username', 'reason')
    readonly_fields = ('submitted_at', 'reviewed_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('staff__user', 'reviewed_by')

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('position', 'start_time', 'end_time', 'staff', 'status', 'is_open')
    list_filter = ('position__department', 'status', 'is_open', 'start_time')
    search_fields = ('staff__user__username', 'position__title', 'notes')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('position', 'staff__user', 'created_by')

@admin.register(ShiftSwapRequest)
class ShiftSwapRequestAdmin(admin.ModelAdmin):
    list_display = ('requested_by', 'requested_to', 'requested_shift', 'status', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('requested_by__user__username', 'requested_to__user__username', 'reason')
    readonly_fields = ('requested_at', 'responded_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'requested_by__user', 'requested_to__user', 'requested_shift', 'offered_shift'
        )

@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ('position', 'day_of_week', 'start_time', 'end_time', 'staff', 'is_active')
    list_filter = ('position__department', 'day_of_week', 'is_active')
    search_fields = ('position__title', 'staff__user__username')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_published', 'created_at')
    list_filter = ('is_published', 'start_date')
    search_fields = ('name', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['publish_schedules', 'unpublish_schedules', 'generate_shifts_from_templates']

    def publish_schedules(self, request, queryset):
        for schedule in queryset:
            schedule.publish()
        self.message_user(request, f"{queryset.count()} schedules published successfully.")
    publish_schedules.short_description = "Publish selected schedules"

    def unpublish_schedules(self, request, queryset):
        for schedule in queryset:
            schedule.unpublish()
        self.message_user(request, f"{queryset.count()} schedules unpublished successfully.")
    unpublish_schedules.short_description = "Unpublish selected schedules"

    def generate_shifts_from_templates(self, request, queryset):
        total_shifts = 0
        for schedule in queryset:
            shifts_created = schedule.generate_from_templates()
            total_shifts += shifts_created
        self.message_user(request, f"{total_shifts} shifts generated successfully across {queryset.count()} schedules.")
    generate_shifts_from_templates.short_description = "Generate shifts from templates"

@admin.register(ClockInOut)
class ClockInOutAdmin(admin.ModelAdmin):
    list_display = ('staff', 'record_type', 'timestamp', 'shift')
    list_filter = ('record_type', 'timestamp')
    search_fields = ('staff__user__username', 'notes')
    readonly_fields = ('timestamp',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('staff__user', 'shift')

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'status', 'processed_by', 'processed_at')
    list_filter = ('status', 'start_date')
    search_fields = ('notes',)
    readonly_fields = ('processed_at',)
    actions = ['close_periods', 'mark_periods_as_paid']

    def close_periods(self, request, queryset):
        for period in queryset.filter(status='open'):
            period.close(request.user)
        self.message_user(request, f"Selected open periods have been closed.")
    close_periods.short_description = "Close selected open periods"

    def mark_periods_as_paid(self, request, queryset):
        for period in queryset.filter(status='closed'):
            period.mark_as_paid(request.user)
        self.message_user(request, f"Selected closed periods have been marked as paid.")
    mark_periods_as_paid.short_description = "Mark selected closed periods as paid"

class PayrollRecordInline(admin.TabularInline):
    model = PayrollRecord
    extra = 0
    readonly_fields = ('gross_pay', 'net_pay')

@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ('staff', 'payroll_period', 'regular_hours', 'overtime_hours', 'gross_pay', 'net_pay')
    list_filter = ('payroll_period__status', 'payroll_period__start_date')
    search_fields = ('staff__user__username', 'notes')
    readonly_fields = ('gross_pay', 'net_pay')
    actions = ['calculate_pay']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('staff__user', 'payroll_period')

    def calculate_pay(self, request, queryset):
        for record in queryset:
            record.calculate_pay()
        self.message_user(request, f"Pay calculated for {queryset.count()} payroll records.")
    calculate_pay.short_description = "Calculate pay for selected records"
