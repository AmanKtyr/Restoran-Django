from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
import csv
import json

from .models import (
    DailySalesReport, MenuItemPerformance, CategoryPerformance,
    HourlySalesData, CustomerAnalytics, MarketingCampaign, CampaignPerformance
)
from orders.models import Order, OrderItem
from menu.models import MenuItem, Category

# Helper function to check if user is staff or admin
def is_staff_or_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_admin)
def analytics_dashboard(request):
    """Main analytics dashboard view"""
    # Get date range for analytics
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get sales data
    total_sales = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='completed',
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0

    # Get order data
    total_orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='completed'
    ).count()

    # Get customer data
    total_customers = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        user__isnull=False
    ).values('user').distinct().count()

    # Get average order value
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0

    # Get top selling menu items
    top_items = OrderItem.objects.filter(
        order__created_at__date__range=[start_date, end_date],
        order__status='completed'
    ).values('menu_item__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'avg_order_value': avg_order_value,
        'top_items': top_items,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'analytics/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def sales_analytics(request):
    """View sales analytics"""
    # Get date range for analytics
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get custom date range if provided
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    if custom_start and custom_end:
        try:
            start_date = timezone.datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(custom_end, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Get daily sales data
    daily_sales = DailySalesReport.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')

    # Prepare data for charts
    dates = [item.date.strftime('%Y-%m-%d') for item in daily_sales]
    sales_values = [float(item.total_sales) for item in daily_sales]
    order_counts = [item.total_orders for item in daily_sales]

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'daily_sales': daily_sales,
        'dates_json': json.dumps(dates),
        'sales_json': json.dumps(sales_values),
        'orders_json': json.dumps(order_counts),
    }
    return render(request, 'analytics/sales.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def customer_analytics(request):
    """View customer analytics"""
    # Get date range for analytics
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get custom date range if provided
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    if custom_start and custom_end:
        try:
            start_date = timezone.datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(custom_end, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Get customer analytics data
    customer_data = CustomerAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')

    # Prepare data for charts
    dates = [item.date.strftime('%Y-%m-%d') for item in customer_data]
    new_customers = [item.new_customers for item in customer_data]
    returning_customers = [item.returning_customers for item in customer_data]

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'customer_data': customer_data,
        'dates_json': json.dumps(dates),
        'new_customers_json': json.dumps(new_customers),
        'returning_customers_json': json.dumps(returning_customers),
    }
    return render(request, 'analytics/customers.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def menu_analytics(request):
    """View menu analytics"""
    # Get date range for analytics
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get custom date range if provided
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    if custom_start and custom_end:
        try:
            start_date = timezone.datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(custom_end, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Get top selling menu items
    top_items = MenuItemPerformance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('menu_item').order_by('-quantity_sold')[:10]

    # Get sales by category
    category_sales = CategoryPerformance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('category').order_by('-total_sales')

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'top_items': top_items,
        'category_sales': category_sales,
    }
    return render(request, 'analytics/menu.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def marketing_analytics(request):
    """View marketing analytics"""
    # Get all marketing campaigns
    campaigns = MarketingCampaign.objects.all().order_by('-start_date')

    # Get campaign performance data
    campaign_id = request.GET.get('campaign')
    if campaign_id:
        campaign = MarketingCampaign.objects.get(id=campaign_id)
        performance_data = CampaignPerformance.objects.filter(campaign=campaign).order_by('date')
    else:
        campaign = None
        performance_data = None

    context = {
        'campaigns': campaigns,
        'selected_campaign': campaign,
        'performance_data': performance_data,
    }
    return render(request, 'analytics/marketing.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def reports(request):
    """View and generate reports"""
    report_type = request.GET.get('type', 'sales')

    # Get date range for report
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get custom date range if provided
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    if custom_start and custom_end:
        try:
            start_date = timezone.datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(custom_end, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Generate report data based on type
    if report_type == 'sales':
        report_data = DailySalesReport.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
    elif report_type == 'menu':
        report_data = MenuItemPerformance.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('menu_item').order_by('-quantity_sold')
    elif report_type == 'customers':
        report_data = CustomerAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
    else:
        report_data = []

    context = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'report_data': report_data,
    }
    return render(request, 'analytics/reports.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def export_report(request, report_type):
    """Export report data as CSV"""
    # Get date range for report
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get custom date range if provided
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    if custom_start and custom_end:
        try:
            start_date = timezone.datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(custom_end, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{start_date}_to_{end_date}.csv"'

    writer = csv.writer(response)

    # Generate CSV data based on report type
    if report_type == 'sales':
        writer.writerow(['Date', 'Total Sales', 'Order Count', 'Average Order Value'])

        report_data = DailySalesReport.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')

        for item in report_data:
            writer.writerow([
                item.date,
                item.total_sales,
                item.total_orders,
                item.average_order_value
            ])

    elif report_type == 'menu':
        writer.writerow(['Item Name', 'Category', 'Quantity Sold', 'Total Revenue'])

        report_data = MenuItemPerformance.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('menu_item').order_by('-quantity_sold')

        for item in report_data:
            writer.writerow([
                item.menu_item.name,
                item.menu_item.category.name if item.menu_item.category else 'No Category',
                item.quantity_sold,
                item.total_sales
            ])

    elif report_type == 'customers':
        writer.writerow(['Date', 'New Customers', 'Returning Customers', 'Total Customers'])

        report_data = CustomerAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')

        for item in report_data:
            writer.writerow([
                item.date,
                item.new_customers,
                item.returning_customers,
                item.total_customers
            ])

    return response
