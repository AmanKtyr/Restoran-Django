from django.db import models
from django.contrib.auth.models import User
from menu.models import MenuItem
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'menu_item')

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"

    def get_total_price(self):
        return self.menu_item.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup/Delivery'),
        ('on_the_way', 'On the Way'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    ORDER_TYPE_CHOICES = (
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('dine_in', 'Dine In'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('apple_pay', 'Apple Pay'),
        ('google_pay', 'Google Pay'),
        ('bank_transfer', 'Bank Transfer'),
        ('in_store', 'In-Store Payment'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    )

    PRIORITY_CHOICES = (
        (1, 'Low'),
        (2, 'Normal'),
        (3, 'High'),
        (4, 'Urgent'),
    )

    # Basic information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='delivery')
    priority = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES, default=2, help_text="Order priority level")
    is_gift = models.BooleanField(default=False, help_text="Whether this order is a gift")
    gift_message = models.TextField(blank=True, help_text="Message to include with gift")

    # Payment information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Payment gateway transaction ID")
    payment_date = models.DateTimeField(null=True, blank=True)

    # Customer information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Delivery information
    address = models.TextField(blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='United States')
    delivery_notes = models.TextField(blank=True, help_text="Special instructions for delivery")

    # Table information (for dine-in)
    table_number = models.CharField(max_length=10, blank=True, help_text="Table number for dine-in orders")
    number_of_guests = models.PositiveSmallIntegerField(default=1, help_text="Number of guests for dine-in orders")

    # Order details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Additional service fee")
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    preparation_started_at = models.DateTimeField(null=True, blank=True)
    ready_for_pickup_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    preparation_time_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Actual preparation time in minutes")

    # Delivery/fulfillment information
    tracking_number = models.CharField(max_length=50, blank=True)
    delivery_provider = models.CharField(max_length=100, blank=True, help_text="Delivery service provider")
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    delivery_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Additional information
    notes = models.TextField(blank=True, help_text="Internal notes about the order")
    special_request = models.TextField(blank=True, help_text="Customer's special requests")
    source = models.CharField(max_length=50, blank=True, help_text="Order source (website, app, phone, etc.)")
    is_first_order = models.BooleanField(default=False, help_text="Whether this is the customer's first order")
    rating = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="Customer rating for this order")
    feedback = models.TextField(blank=True, help_text="Customer feedback about this order")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate a unique order number based on timestamp
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            user_id = self.user.id if self.user else 'GUEST'
            self.order_number = f"ORD-{timestamp}-{user_id}"

            # Check if this is the user's first order
            if self.user and not self.user.orders.exists():
                self.is_first_order = True

        # Update status timestamps
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        elif self.status == 'preparing' and not self.preparation_started_at:
            self.preparation_started_at = timezone.now()
        elif self.status == 'ready' and not self.ready_for_pickup_at and self.order_type == 'pickup':
            self.ready_for_pickup_at = timezone.now()
        elif self.status == 'on_the_way' and not self.out_for_delivery_at and self.order_type == 'delivery':
            self.out_for_delivery_at = timezone.now()
        elif self.status == 'delivered' and not self.actual_delivery_time:
            self.actual_delivery_time = timezone.now()
            self.completed_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()

        # Update payment timestamp
        if self.payment_status == 'paid' and not self.payment_date:
            self.payment_date = timezone.now()

        super().save(*args, **kwargs)

    def get_status_color(self):
        """Get the Bootstrap color class for the current status"""
        status_colors = {
            'pending': 'secondary',
            'confirmed': 'info',
            'preparing': 'primary',
            'ready': 'warning',
            'on_the_way': 'warning',
            'delivered': 'success',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return status_colors.get(self.status, 'secondary')

    def get_progress_percentage(self):
        """Calculate the percentage of completion for the order process"""
        # Define the stages and their weights based on order type
        if self.order_type == 'delivery':
            stages = {
                'pending': 0,
                'confirmed': 20,
                'preparing': 40,
                'ready': 60,
                'on_the_way': 80,
                'delivered': 100,
                'completed': 100,
                'cancelled': 0
            }
        else:  # pickup or dine_in
            stages = {
                'pending': 0,
                'confirmed': 25,
                'preparing': 50,
                'ready': 75,
                'completed': 100,
                'cancelled': 0
            }
        return stages.get(self.status, 0)

    def get_subtotal(self):
        """Calculate the subtotal of all order items"""
        return sum(item.get_total_price() for item in self.items.all())

    def recalculate_total(self):
        """Recalculate the order total"""
        self.subtotal = self.get_subtotal()
        self.total = self.subtotal + self.tax + self.delivery_fee + self.service_fee + self.tip_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'total'])
        return self.total

    def get_estimated_delivery_time(self):
        """Calculate the estimated delivery time based on order type and status"""
        if self.estimated_delivery_time:
            return self.estimated_delivery_time

        if not self.confirmed_at:
            return None

        # Base preparation time in minutes
        prep_time = 20  # Default 20 minutes for preparation

        # Add delivery time if applicable
        if self.order_type == 'delivery':
            delivery_time = 30  # Default 30 minutes for delivery
            total_minutes = prep_time + delivery_time
        else:  # pickup or dine_in
            total_minutes = prep_time

        # Adjust based on priority
        if self.priority == 3:  # High
            total_minutes = int(total_minutes * 0.8)  # 20% faster
        elif self.priority == 4:  # Urgent
            total_minutes = int(total_minutes * 0.6)  # 40% faster
        elif self.priority == 1:  # Low
            total_minutes = int(total_minutes * 1.2)  # 20% slower

        # Calculate the estimated time
        base_time = self.confirmed_at or self.created_at
        estimated_time = base_time + timezone.timedelta(minutes=total_minutes)

        # Update the model
        self.estimated_delivery_time = estimated_time
        self.save(update_fields=['estimated_delivery_time'])

        return estimated_time

    def mark_as_delivered(self):
        """Mark the order as delivered"""
        self.status = 'delivered'
        self.actual_delivery_time = timezone.now()
        self.save(update_fields=['status', 'actual_delivery_time'])

    def cancel_order(self, reason=None):
        """Cancel the order"""
        self.status = 'cancelled'
        if reason:
            self.notes = f"Cancelled: {reason}\n" + self.notes
        self.save(update_fields=['status', 'notes'])

    def get_delivery_status_display(self):
        """Get a user-friendly delivery status message"""
        if self.status == 'pending':
            return "Your order has been received and is awaiting confirmation."
        elif self.status == 'confirmed':
            return "Your order has been confirmed and will be prepared soon."
        elif self.status == 'preparing':
            return "Your order is being prepared in our kitchen."
        elif self.status == 'ready':
            if self.order_type == 'delivery':
                return "Your order is ready and waiting for pickup by our delivery driver."
            else:
                return "Your order is ready for pickup."
        elif self.status == 'on_the_way':
            return f"Your order is on the way! Estimated delivery time: {self.estimated_delivery_time.strftime('%H:%M')}"
        elif self.status == 'delivered':
            return "Your order has been delivered. Enjoy your meal!"
        elif self.status == 'completed':
            return "Your order has been completed. Thank you for your business!"
        elif self.status == 'cancelled':
            return "Your order has been cancelled."
        return "Order status unknown."

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of order
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Cost price at the time of order
    special_instructions = models.TextField(blank=True)
    customizations = models.JSONField(null=True, blank=True, help_text="JSON field for storing customizations")
    is_free = models.BooleanField(default=False, help_text="Whether this item is free (e.g., promotion)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount amount for this item")
    discount_reason = models.CharField(max_length=100, blank=True, help_text="Reason for the discount")
    is_voided = models.BooleanField(default=False, help_text="Whether this item was voided")
    void_reason = models.CharField(max_length=100, blank=True, help_text="Reason for voiding this item")

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"

    def get_total_price(self):
        """Calculate the total price for this item"""
        if self.is_free or self.is_voided:
            return 0
        return (self.price * self.quantity) - self.discount_amount

    def get_profit(self):
        """Calculate the profit for this item"""
        if self.is_free or self.is_voided or not self.cost_price:
            return 0
        return self.get_total_price() - (self.cost_price * self.quantity)

    def get_profit_margin(self):
        """Calculate the profit margin percentage"""
        total_price = self.get_total_price()
        if total_price <= 0 or not self.cost_price:
            return 0

        total_cost = self.cost_price * self.quantity
        profit = total_price - total_cost
        return (profit / total_price) * 100

    def void_item(self, reason):
        """Void this item"""
        self.is_voided = True
        self.void_reason = reason
        self.save(update_fields=['is_voided', 'void_reason'])

        # Recalculate order total
        self.order.recalculate_total()

    def apply_discount(self, amount, reason):
        """Apply a discount to this item"""
        self.discount_amount = amount
        self.discount_reason = reason
        self.save(update_fields=['discount_amount', 'discount_reason'])

        # Recalculate order total
        self.order.recalculate_total()
