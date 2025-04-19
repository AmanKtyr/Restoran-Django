from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from menu.models import MenuItem, Category
from orders.models import Order, OrderItem

class DailySalesReport(models.Model):
    """Represents a daily sales report"""
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_discounts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Daily Sales Reports"

    def __str__(self):
        return f"Sales Report for {self.date} - ${self.total_sales}"

    @classmethod
    def generate_for_date(cls, date):
        """Generate a sales report for a specific date"""
        # Get all completed orders for the date
        orders = Order.objects.filter(
            created_at__date=date,
            status='completed',
            payment_status='paid'
        )

        # Calculate metrics
        total_sales = sum(order.total for order in orders)
        total_orders = orders.count()
        average_order_value = total_sales / total_orders if total_orders > 0 else 0
        total_tax = sum(order.tax for order in orders)
        total_discounts = sum(order.discount_amount for order in orders)

        # Create or update the report
        report, created = cls.objects.update_or_create(
            date=date,
            defaults={
                'total_sales': total_sales,
                'total_orders': total_orders,
                'average_order_value': average_order_value,
                'total_tax': total_tax,
                'total_discounts': total_discounts
            }
        )

        return report

class MenuItemPerformance(models.Model):
    """Represents the performance of a menu item"""
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='performance_records')
    date = models.DateField()
    quantity_sold = models.PositiveIntegerField(default=0)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_of_goods = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage

    class Meta:
        unique_together = ('menu_item', 'date')
        ordering = ['-date', '-quantity_sold']

    def __str__(self):
        return f"{self.menu_item.name} - {self.date} - {self.quantity_sold} sold"

    @classmethod
    def generate_for_date(cls, date):
        """Generate performance records for all menu items for a specific date"""
        # Get all completed orders for the date
        orders = Order.objects.filter(
            created_at__date=date,
            status='completed',
            payment_status='paid'
        )

        # Get all order items from these orders
        order_items = OrderItem.objects.filter(order__in=orders)

        # Group by menu item and calculate metrics
        menu_item_data = {}
        for item in order_items:
            if item.menu_item_id not in menu_item_data:
                menu_item_data[item.menu_item_id] = {
                    'quantity': 0,
                    'sales': 0,
                }

            menu_item_data[item.menu_item_id]['quantity'] += item.quantity
            menu_item_data[item.menu_item_id]['sales'] += item.get_subtotal()

        # Create or update performance records
        records = []
        for menu_item_id, data in menu_item_data.items():
            try:
                menu_item = MenuItem.objects.get(id=menu_item_id)
                cost = menu_item.cost_price * data['quantity'] if menu_item.cost_price else 0
                profit = data['sales'] - cost
                margin = (profit / data['sales'] * 100) if data['sales'] > 0 else 0

                record, created = cls.objects.update_or_create(
                    menu_item=menu_item,
                    date=date,
                    defaults={
                        'quantity_sold': data['quantity'],
                        'total_sales': data['sales'],
                        'cost_of_goods': cost,
                        'profit_margin': margin
                    }
                )
                records.append(record)
            except MenuItem.DoesNotExist:
                continue

        return records

class CategoryPerformance(models.Model):
    """Represents the performance of a menu category"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='performance_records')
    date = models.DateField()
    quantity_sold = models.PositiveIntegerField(default=0)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    percentage_of_sales = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage

    class Meta:
        unique_together = ('category', 'date')
        ordering = ['-date', '-total_sales']
        verbose_name_plural = "Category Performances"

    def __str__(self):
        return f"{self.category.name} - {self.date} - ${self.total_sales}"

    @classmethod
    def generate_for_date(cls, date):
        """Generate performance records for all categories for a specific date"""
        # Get the daily sales report for the date
        try:
            daily_report = DailySalesReport.objects.get(date=date)
            total_daily_sales = daily_report.total_sales
        except DailySalesReport.DoesNotExist:
            # Generate the daily report if it doesn't exist
            daily_report = DailySalesReport.generate_for_date(date)
            total_daily_sales = daily_report.total_sales

        # Get all menu item performances for the date
        menu_item_performances = MenuItemPerformance.objects.filter(date=date)

        # Group by category and calculate metrics
        category_data = {}
        for performance in menu_item_performances:
            category_id = performance.menu_item.category_id
            if category_id not in category_data:
                category_data[category_id] = {
                    'quantity': 0,
                    'sales': 0,
                }

            category_data[category_id]['quantity'] += performance.quantity_sold
            category_data[category_id]['sales'] += performance.total_sales

        # Create or update category performance records
        records = []
        for category_id, data in category_data.items():
            try:
                category = Category.objects.get(id=category_id)
                percentage = (data['sales'] / total_daily_sales * 100) if total_daily_sales > 0 else 0

                record, created = cls.objects.update_or_create(
                    category=category,
                    date=date,
                    defaults={
                        'quantity_sold': data['quantity'],
                        'total_sales': data['sales'],
                        'percentage_of_sales': percentage
                    }
                )
                records.append(record)
            except Category.DoesNotExist:
                continue

        return records

class HourlySalesData(models.Model):
    """Represents sales data for each hour of the day"""
    date = models.DateField()
    hour = models.PositiveSmallIntegerField()  # 0-23
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_count = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('date', 'hour')
        ordering = ['date', 'hour']
        verbose_name_plural = "Hourly Sales Data"

    def __str__(self):
        return f"{self.date} - {self.hour}:00 - ${self.total_sales}"

    @classmethod
    def generate_for_date(cls, date):
        """Generate hourly sales data for a specific date"""
        records = []

        # For each hour of the day (0-23)
        for hour in range(24):
            # Get all completed orders for the date and hour
            orders = Order.objects.filter(
                created_at__date=date,
                created_at__hour=hour,
                status='completed',
                payment_status='paid'
            )

            # Calculate metrics
            total_sales = sum(order.total for order in orders)
            order_count = orders.count()
            average_order_value = total_sales / order_count if order_count > 0 else 0

            # Create or update the hourly record
            record, created = cls.objects.update_or_create(
                date=date,
                hour=hour,
                defaults={
                    'total_sales': total_sales,
                    'order_count': order_count,
                    'average_order_value': average_order_value
                }
            )
            records.append(record)

        return records

class CustomerAnalytics(models.Model):
    """Represents analytics data for customers"""
    date = models.DateField(unique=True)
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    total_customers = models.PositiveIntegerField(default=0)
    average_order_value_new = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_order_value_returning = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Customer Analytics"

    def __str__(self):
        return f"Customer Analytics for {self.date}"

    @classmethod
    def generate_for_date(cls, date):
        """Generate customer analytics for a specific date"""
        # Get all completed orders for the date
        orders = Order.objects.filter(
            created_at__date=date,
            status='completed',
            payment_status='paid'
        )

        # Get all users who placed orders on this date
        users_today = set(order.user_id for order in orders if order.user_id is not None)

        # Get all users who placed orders before this date
        previous_users = set(Order.objects.filter(
            created_at__date__lt=date,
            user__isnull=False
        ).values_list('user_id', flat=True).distinct())

        # Calculate new vs returning customers
        new_customers = users_today - previous_users
        returning_customers = users_today & previous_users

        # Calculate average order values
        new_customer_orders = orders.filter(user_id__in=new_customers)
        returning_customer_orders = orders.filter(user_id__in=returning_customers)

        avg_new = sum(order.total for order in new_customer_orders) / new_customer_orders.count() if new_customer_orders.count() > 0 else 0
        avg_returning = sum(order.total for order in returning_customer_orders) / returning_customer_orders.count() if returning_customer_orders.count() > 0 else 0

        # Create or update the analytics record
        record, created = cls.objects.update_or_create(
            date=date,
            defaults={
                'new_customers': len(new_customers),
                'returning_customers': len(returning_customers),
                'total_customers': len(users_today),
                'average_order_value_new': avg_new,
                'average_order_value_returning': avg_returning
            }
        )

        return record

class MarketingCampaign(models.Model):
    """Represents a marketing campaign"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    target_audience = models.CharField(max_length=100, blank=True)
    promotion_code = models.CharField(max_length=50, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

class CampaignPerformance(models.Model):
    """Represents the performance of a marketing campaign"""
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name='performance_records')
    date = models.DateField()
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    roi = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Return on Investment

    class Meta:
        unique_together = ('campaign', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.campaign.name} - {self.date} - ROI: {self.roi}%"

    def calculate_roi(self):
        """Calculate the ROI for this campaign performance"""
        if self.cost > 0:
            self.roi = ((self.revenue - self.cost) / self.cost) * 100
        else:
            self.roi = 0
        return self.roi

    def save(self, *args, **kwargs):
        self.calculate_roi()
        super().save(*args, **kwargs)
