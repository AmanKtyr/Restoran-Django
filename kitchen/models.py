from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from orders.models import Order, OrderItem

class KitchenStation(models.Model):
    """Represents a station in the kitchen (e.g., grill, fry, salad, etc.)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['display_order', 'name']

class KitchenDisplay(models.Model):
    """Represents a physical display in the kitchen"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    stations = models.ManyToManyField(KitchenStation, related_name='displays')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class MenuItemStation(models.Model):
    """Maps menu items to kitchen stations"""
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE, related_name='kitchen_stations')
    station = models.ForeignKey(KitchenStation, on_delete=models.CASCADE, related_name='menu_items')
    preparation_time_minutes = models.PositiveIntegerField(default=10, help_text="Estimated preparation time in minutes")

    class Meta:
        unique_together = ('menu_item', 'station')

    def __str__(self):
        return f"{self.menu_item.name} - {self.station.name}"

class OrderItemStatus(models.Model):
    """Tracks the status of each order item in the kitchen"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='kitchen_status')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    station = models.ForeignKey(KitchenStation, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_order_items')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_completion_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.order_item} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Update timestamps based on status changes
        if self.status == 'in_progress' and not self.started_at:
            self.started_at = timezone.now()

            # Calculate estimated completion time
            if not self.estimated_completion_time:
                prep_time = 10  # Default 10 minutes

                # Try to get the preparation time from MenuItemStation
                try:
                    menu_item_station = MenuItemStation.objects.get(
                        menu_item=self.order_item.menu_item,
                        station=self.station
                    )
                    prep_time = menu_item_station.preparation_time_minutes
                except MenuItemStation.DoesNotExist:
                    pass

                self.estimated_completion_time = self.started_at + timezone.timedelta(minutes=prep_time)

        elif self.status == 'ready' and not self.completed_at:
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)

        # Check if all items in the order are ready
        self.check_order_status()

    def check_order_status(self):
        """Check if all items in the order are ready and update the order status accordingly"""
        order = self.order_item.order

        # Skip if the order is already completed or cancelled
        if order.status in ['completed', 'cancelled']:
            return

        # Get all order items for this order
        order_items = order.items.all()

        # Check if all items have kitchen status
        all_have_status = True
        all_ready = True
        all_delivered = True

        for item in order_items:
            try:
                kitchen_status = item.kitchen_status
                if kitchen_status.status != 'ready':
                    all_ready = False
                if kitchen_status.status != 'delivered':
                    all_delivered = False
            except OrderItemStatus.DoesNotExist:
                all_have_status = False
                all_ready = False
                all_delivered = False
                break

        # Update order status if all items are ready
        if all_have_status and all_ready and order.status not in ['ready', 'on_the_way', 'delivered', 'completed']:
            order.status = 'ready'
            order.save(update_fields=['status'])

        # Update order status if all items are delivered
        elif all_have_status and all_delivered and order.status not in ['delivered', 'completed']:
            order.status = 'delivered'
            order.actual_delivery_time = timezone.now()
            order.save(update_fields=['status', 'actual_delivery_time'])

class KitchenLog(models.Model):
    """Logs events in the kitchen"""
    EVENT_TYPES = (
        ('status_change', 'Status Change'),
        ('assignment', 'Assignment'),
        ('note', 'Note'),
        ('alert', 'Alert'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='kitchen_logs')
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='kitchen_logs')
    station = models.ForeignKey(KitchenStation, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kitchen_logs')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    event_description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class KitchenAlert(models.Model):
    """Represents alerts in the kitchen"""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    title = models.CharField(max_length=100)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    stations = models.ManyToManyField(KitchenStation, blank=True, related_name='alerts')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_expired(self):
        """Check if the alert is expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
