from django.contrib import admin
from django.utils import timezone
from .models import (
    DailySalesReport, MenuItemPerformance, CategoryPerformance,
    HourlySalesData, CustomerAnalytics, MarketingCampaign, CampaignPerformance
)

@admin.register(DailySalesReport)
class DailySalesReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_sales', 'total_orders', 'average_order_value', 'total_tax', 'total_discounts')
    list_filter = ('date',)
    search_fields = ('date',)
    readonly_fields = ('generated_at', 'updated_at')
    date_hierarchy = 'date'
    actions = ['generate_report_for_yesterday', 'generate_report_for_last_week']

    def generate_report_for_yesterday(self, request, queryset):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        report = DailySalesReport.generate_for_date(yesterday)
        self.message_user(request, f"Generated sales report for {yesterday}: ${report.total_sales}")
    generate_report_for_yesterday.short_description = "Generate report for yesterday"

    def generate_report_for_last_week(self, request, queryset):
        today = timezone.now().date()
        reports_generated = 0
        total_sales = 0

        for i in range(1, 8):
            date = today - timezone.timedelta(days=i)
            report = DailySalesReport.generate_for_date(date)
            reports_generated += 1
            total_sales += report.total_sales

        self.message_user(request, f"Generated {reports_generated} sales reports for the last week. Total sales: ${total_sales}")
    generate_report_for_last_week.short_description = "Generate reports for last week"

@admin.register(MenuItemPerformance)
class MenuItemPerformanceAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'date', 'quantity_sold', 'total_sales', 'cost_of_goods', 'profit_margin')
    list_filter = ('date', 'menu_item__category')
    search_fields = ('menu_item__name',)
    date_hierarchy = 'date'
    actions = ['generate_performance_for_yesterday']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('menu_item')

    def generate_performance_for_yesterday(self, request, queryset):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        records = MenuItemPerformance.generate_for_date(yesterday)
        self.message_user(request, f"Generated performance records for {len(records)} menu items for {yesterday}")
    generate_performance_for_yesterday.short_description = "Generate performance for yesterday"

@admin.register(CategoryPerformance)
class CategoryPerformanceAdmin(admin.ModelAdmin):
    list_display = ('category', 'date', 'quantity_sold', 'total_sales', 'percentage_of_sales')
    list_filter = ('date', 'category')
    search_fields = ('category__name',)
    date_hierarchy = 'date'
    actions = ['generate_performance_for_yesterday']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

    def generate_performance_for_yesterday(self, request, queryset):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        records = CategoryPerformance.generate_for_date(yesterday)
        self.message_user(request, f"Generated performance records for {len(records)} categories for {yesterday}")
    generate_performance_for_yesterday.short_description = "Generate performance for yesterday"

@admin.register(HourlySalesData)
class HourlySalesDataAdmin(admin.ModelAdmin):
    list_display = ('date', 'hour', 'total_sales', 'order_count', 'average_order_value')
    list_filter = ('date', 'hour')
    date_hierarchy = 'date'
    actions = ['generate_data_for_yesterday']

    def generate_data_for_yesterday(self, request, queryset):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        records = HourlySalesData.generate_for_date(yesterday)
        self.message_user(request, f"Generated hourly sales data for {yesterday} ({len(records)} hours)")
    generate_data_for_yesterday.short_description = "Generate data for yesterday"

@admin.register(CustomerAnalytics)
class CustomerAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'new_customers', 'returning_customers', 'total_customers',
                   'average_order_value_new', 'average_order_value_returning')
    list_filter = ('date',)
    date_hierarchy = 'date'
    actions = ['generate_analytics_for_yesterday']

    def generate_analytics_for_yesterday(self, request, queryset):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        record = CustomerAnalytics.generate_for_date(yesterday)
        self.message_user(request, f"Generated customer analytics for {yesterday}: {record.total_customers} customers")
    generate_analytics_for_yesterday.short_description = "Generate analytics for yesterday"

@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'budget', 'promotion_code', 'discount_percentage', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('name', 'description', 'promotion_code')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

class CampaignPerformanceInline(admin.TabularInline):
    model = CampaignPerformance
    extra = 0
    readonly_fields = ('roi',)

@admin.register(CampaignPerformance)
class CampaignPerformanceAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'date', 'impressions', 'clicks', 'conversions', 'revenue', 'cost', 'roi')
    list_filter = ('date', 'campaign')
    search_fields = ('campaign__name',)
    readonly_fields = ('roi',)
    date_hierarchy = 'date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign')
