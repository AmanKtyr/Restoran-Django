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

class BookingSettings(models.Model):
    """Global settings for the booking system"""
    min_booking_notice_hours = models.PositiveIntegerField(default=1, help_text="Minimum hours in advance for a booking")
    max_booking_days_ahead = models.PositiveIntegerField(default=30, help_text="Maximum days in advance for a booking")
    default_booking_duration_mins = models.PositiveIntegerField(default=120, help_text="Default reservation duration in minutes")
    auto_confirm_bookings = models.BooleanField(default=False, help_text="Automatically confirm bookings")
    send_confirmation_emails = models.BooleanField(default=True)
    send_reminder_emails = models.BooleanField(default=True)
    reminder_hours_before = models.PositiveIntegerField(default=24, help_text="Hours before reservation to send reminder")
    max_party_size = models.PositiveIntegerField(default=20, help_text="Maximum number of guests per booking")
    min_party_size = models.PositiveIntegerField(default=1, help_text="Minimum number of guests per booking")
    allow_online_cancellation = models.BooleanField(default=True)
    cancellation_deadline_hours = models.PositiveIntegerField(default=24, help_text="Hours before reservation when cancellation is no longer allowed")
    require_deposit = models.BooleanField(default=False, help_text="Require a deposit for reservations")
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deposit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Percentage of estimated bill")

    class Meta:
        verbose_name = 'Booking Settings'
        verbose_name_plural = 'Booking Settings'

    def __str__(self):
        return "Booking System Settings"

class SpecialDate(models.Model):
    """Special dates like holidays or events that affect booking availability"""
    name = models.CharField(max_length=100)
    date = models.DateField()
    is_closed = models.BooleanField(default=False, help_text="Restaurant is closed on this date")
    has_special_hours = models.BooleanField(default=False)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    max_bookings = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of bookings allowed on this date")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} - {self.date}"

class TimeSlot(models.Model):
    """Represents available time slots for bookings"""
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_bookings = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ('day_of_week', 'start_time')

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('seated', 'Seated'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )

    SOURCE_CHOICES = (
        ('website', 'Website'),
        ('phone', 'Phone'),
        ('walk_in', 'Walk-in'),
        ('third_party', 'Third Party App'),
        ('opentable', 'OpenTable'),
        ('resy', 'Resy'),
        ('yelp', 'Yelp'),
        ('google', 'Google'),
    )

    DEPOSIT_STATUS_CHOICES = (
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('forfeited', 'Forfeited'),
    )

    # Basic information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    guest_count_adults = models.PositiveIntegerField(default=2, validators=[MinValueValidator(1)])
    guest_count_children = models.PositiveIntegerField(default=0)
    guest_count_infants = models.PositiveIntegerField(default=0)
    is_vip = models.BooleanField(default=False)
    vip_notes = models.TextField(blank=True)

    # Reservation details
    date_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=120)
    tables = models.ManyToManyField(Table, blank=True, related_name='bookings')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    occasion = models.CharField(max_length=100, blank=True, help_text="E.g., Birthday, Anniversary")
    special_request = models.TextField(blank=True)
    dietary_requirements = models.TextField(blank=True)
    preferred_seating_area = models.CharField(max_length=50, choices=[
        ('no_preference', 'No Preference'),
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('bar', 'Bar'),
        ('private', 'Private Room'),
        ('window', 'Window'),
        ('quiet', 'Quiet Area'),
    ], default='no_preference')

    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')
    confirmation_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    feedback_requested = models.BooleanField(default=False)
    feedback_requested_at = models.DateTimeField(null=True, blank=True)
    deposit_status = models.CharField(max_length=20, choices=DEPOSIT_STATUS_CHOICES, default='not_required')
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deposit_transaction_id = models.CharField(max_length=100, blank=True)
    deposit_paid_at = models.DateTimeField(null=True, blank=True)
    assigned_server = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bookings')
    actual_guest_count = models.PositiveIntegerField(null=True, blank=True)
    table_assignment_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    seated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancellation_by = models.CharField(max_length=50, blank=True, help_text="Who cancelled the booking (customer, staff, system)")
    no_show_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_time']
        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'

    def __str__(self):
        return f"{self.name} - {self.date_time.strftime('%Y-%m-%d %H:%M')} - {self.get_total_guests()} guests"

    def get_total_guests(self):
        """Calculate the total number of guests"""
        return self.guest_count_adults + self.guest_count_children + self.guest_count_infants

    def get_duration_minutes(self):
        """Calculate the reservation duration in minutes"""
        if self.end_time:
            delta = self.end_time - self.date_time
            return delta.seconds // 60
        return self.duration_minutes

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

    def mark_as_confirmed(self, by_user=None):
        """Mark the booking as confirmed"""
        from django.utils import timezone
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at'])

    def mark_as_seated(self, by_user=None, actual_guest_count=None):
        """Mark the booking as seated"""
        from django.utils import timezone
        self.status = 'seated'
        self.seated_at = timezone.now()
        if actual_guest_count is not None:
            self.actual_guest_count = actual_guest_count
        self.save(update_fields=['status', 'seated_at', 'actual_guest_count'])

    def mark_as_completed(self, by_user=None):
        """Mark the booking as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def mark_as_cancelled(self, reason='', by='customer'):
        """Mark the booking as cancelled"""
        from django.utils import timezone
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.cancellation_by = by
        self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'cancellation_by'])

    def mark_as_no_show(self, by_user=None):
        """Mark the booking as no-show"""
        from django.utils import timezone
        self.status = 'no_show'
        self.no_show_at = timezone.now()
        self.save(update_fields=['status', 'no_show_at'])

    def is_cancellable_online(self):
        """Check if the booking can be cancelled online"""
        from django.utils import timezone
        try:
            settings = BookingSettings.objects.first()
            if not settings.allow_online_cancellation:
                return False

            # Check if it's past the cancellation deadline
            deadline = self.date_time - timezone.timedelta(hours=settings.cancellation_deadline_hours)
            if timezone.now() > deadline:
                return False

            # Can't cancel if already cancelled, completed, or no-show
            if self.status in ['cancelled', 'completed', 'no_show']:
                return False

            return True
        except Exception:
            # Default to allowing cancellation if settings aren't available
            return True

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
