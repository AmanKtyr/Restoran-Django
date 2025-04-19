from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class Supplier(models.Model):
    """Represents a supplier of ingredients and other items"""
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    """Represents a category of inventory items"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Unit(models.Model):
    """Represents a unit of measurement for inventory items"""
    name = models.CharField(max_length=50)  # e.g., kilogram, liter, piece
    abbreviation = models.CharField(max_length=10)  # e.g., kg, L, pc

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class InventoryItem(models.Model):
    """Represents an item in the inventory"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='items')
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    optimal_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateField(null=True, blank=True)
    storage_location = models.CharField(max_length=100, blank=True)
    suppliers = models.ManyToManyField(Supplier, through='SupplierItem', related_name='items')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit.abbreviation})"

    @property
    def stock_status(self):
        """Return the stock status (low, optimal, overstocked)"""
        if self.current_stock <= self.minimum_stock:
            return "low"
        elif self.current_stock <= self.optimal_stock:
            return "optimal"
        else:
            return "overstocked"

    @property
    def needs_reordering(self):
        """Check if the item needs to be reordered"""
        return self.current_stock <= self.minimum_stock

    @property
    def total_value(self):
        """Calculate the total value of the current stock"""
        return self.current_stock * self.cost_per_unit

class SupplierItem(models.Model):
    """Represents the relationship between suppliers and inventory items"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    supplier_item_code = models.CharField(max_length=50, blank=True)
    supplier_price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    lead_time_days = models.PositiveIntegerField(default=1, help_text="Estimated delivery time in days")
    is_preferred_supplier = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    last_ordered_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('supplier', 'item')

    def __str__(self):
        return f"{self.item.name} from {self.supplier.name}"

class StockAdjustment(models.Model):
    """Represents an adjustment to the inventory stock"""
    ADJUSTMENT_TYPES = (
        ('receipt', 'Receipt'),
        ('usage', 'Usage'),
        ('waste', 'Waste'),
        ('return', 'Return to Supplier'),
        ('correction', 'Inventory Correction'),
        ('transfer', 'Transfer'),
    )

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='adjustments')
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    date = models.DateTimeField(default=timezone.now)
    reason = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reference_number = models.CharField(max_length=50, blank=True, help_text="PO number, invoice number, etc.")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_adjustment_type_display()} of {self.quantity} {self.item.unit.abbreviation} of {self.item.name}"

    def save(self, *args, **kwargs):
        # Update the inventory item's current stock
        is_new = self.pk is None

        if is_new:
            # This is a new adjustment
            if self.adjustment_type in ['receipt', 'correction', 'return']:
                self.item.current_stock += self.quantity
            else:  # usage, waste, transfer
                self.item.current_stock -= self.quantity

            # Update the cost per unit for receipts if unit cost is provided
            if self.adjustment_type == 'receipt' and self.unit_cost is not None:
                self.item.cost_per_unit = self.unit_cost

            self.item.save(update_fields=['current_stock', 'cost_per_unit'])

        super().save(*args, **kwargs)

class PurchaseOrder(models.Model):
    """Represents a purchase order to a supplier"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    )

    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_purchase_orders')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    delivery_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PO-{self.order_number} - {self.supplier.name}"

    def calculate_total(self):
        """Calculate the total amount of the purchase order"""
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

class PurchaseOrderItem(models.Model):
    """Represents an item in a purchase order"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('purchase_order', 'item')

    def __str__(self):
        return f"{self.quantity} {self.item.unit.abbreviation} of {self.item.name}"

    @property
    def subtotal(self):
        """Calculate the subtotal for this item"""
        return self.quantity * self.unit_price

    @property
    def is_fully_received(self):
        """Check if the item has been fully received"""
        return self.received_quantity >= self.quantity

class InventoryCheck(models.Model):
    """Represents a physical inventory check/count"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    check_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inventory_checks')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-check_date']

    def __str__(self):
        return f"Inventory Check on {self.check_date}"

    def complete_check(self):
        """Mark the inventory check as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

class InventoryCheckItem(models.Model):
    """Represents an item in an inventory check"""
    inventory_check = models.ForeignKey(InventoryCheck, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    expected_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    actual_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('inventory_check', 'item')

    def __str__(self):
        return f"{self.item.name} in {self.inventory_check}"

    @property
    def discrepancy(self):
        """Calculate the discrepancy between expected and actual quantities"""
        if self.actual_quantity is None:
            return None
        return self.actual_quantity - self.expected_quantity

    @property
    def discrepancy_percentage(self):
        """Calculate the discrepancy as a percentage"""
        if self.actual_quantity is None or self.expected_quantity == 0:
            return None
        return (self.discrepancy / self.expected_quantity) * 100
