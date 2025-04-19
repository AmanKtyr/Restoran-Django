from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Table(models.Model):
    table_number = models.IntegerField(unique=True)
    capacity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    location = models.CharField(max_length=50, choices=[
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('bar', 'Bar'),
        ('private', 'Private Room'),
    ], default='indoor')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} seats, {self.get_location_display()})"

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    )

    SOURCE_CHOICES = (
        ('website', 'Website'),
        ('phone', 'Phone'),
        ('walk_in', 'Walk-in'),
        ('third_party', 'Third Party App'),
    )

    # Basic information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)

    # Reservation details
    date_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    num_people = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    tables = models.ManyToManyField(Table, blank=True, related_name='bookings')
    occasion = models.CharField(max_length=100, blank=True, help_text="E.g., Birthday, Anniversary")
    special_request = models.TextField(blank=True)

    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')
    confirmation_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    feedback_requested = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_time']
        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'

    def __str__(self):
        return f"{self.name} - {self.date_time.strftime('%Y-%m-%d %H:%M')} - {self.num_people} people"

    def get_duration_minutes(self):
        """Calculate the reservation duration in minutes"""
        if not self.end_time:
            # Default to 2 hours if no end time is specified
            return 120

        delta = self.end_time - self.date_time
        return delta.seconds // 60

    def generate_confirmation_code(self):
        """Generate a unique confirmation code for the booking"""
        import uuid

        if not self.confirmation_code:
            # Create a code based on date and random string
            date_str = self.date_time.strftime('%y%m%d')
            random_str = str(uuid.uuid4())[:6].upper()
            self.confirmation_code = f"RES-{date_str}-{random_str}"
            self.save(update_fields=['confirmation_code'])

        return self.confirmation_code
