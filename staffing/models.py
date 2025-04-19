from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Department(models.Model):
    """Represents a department in the restaurant"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Position(models.Model):
    """Represents a job position in the restaurant"""
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    description = models.TextField(blank=True)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_full_time = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.department.name})"

class StaffProfile(models.Model):
    """Extends the User model with additional staff information"""
    EMPLOYMENT_STATUS_CHOICES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('seasonal', 'Seasonal'),
        ('intern', 'Intern'),
        ('contractor', 'Contractor'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='full_time')
    hire_date = models.DateField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    max_hours_per_week = models.PositiveIntegerField(default=40)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.position.title if self.position else 'No Position'}"

    @property
    def department(self):
        if self.position:
            return self.position.department
        return None

class Skill(models.Model):
    """Represents a skill that staff members can have"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class StaffSkill(models.Model):
    """Represents a skill that a staff member has"""
    PROFICIENCY_CHOICES = (
        (1, 'Beginner'),
        (2, 'Intermediate'),
        (3, 'Advanced'),
        (4, 'Expert'),
        (5, 'Master'),
    )

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='staff_with_skill')
    proficiency = models.PositiveSmallIntegerField(choices=PROFICIENCY_CHOICES, default=1)
    certified = models.BooleanField(default=False)
    certification_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('staff', 'skill')

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.skill.name} ({self.get_proficiency_display()})"

class Availability(models.Model):
    """Represents a staff member's recurring availability"""
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True, help_text="If unchecked, this represents unavailability")

    class Meta:
        verbose_name_plural = "Availabilities"
        unique_together = ('staff', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        availability_type = "Available" if self.is_available else "Unavailable"
        return f"{self.staff.user.get_full_name()} - {self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')} ({availability_type})"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

class TimeOffRequest(models.Model):
    """Represents a request for time off"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('cancelled', 'Cancelled'),
    )

    TYPE_CHOICES = (
        ('vacation', 'Vacation'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    )

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='time_off_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_time_off_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_request_type_display()} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("End date must be after or equal to start date")

    def approve(self, reviewer):
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

    def deny(self, reviewer, notes=None):
        self.status = 'denied'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_notes'])

    def cancel(self):
        self.status = 'cancelled'
        self.save(update_fields=['status'])

class Shift(models.Model):
    """Represents a work shift"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    )

    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='shifts')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    staff = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='shifts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_shifts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_open = models.BooleanField(default=False, help_text="If true, staff can claim this shift")

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        staff_name = self.staff.user.get_full_name() if self.staff else "Unassigned"
        return f"{self.position.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')} to {self.end_time.strftime('%H:%M')} - {staff_name}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

    @property
    def duration_hours(self):
        """Calculate the duration of the shift in hours"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600

    def assign_staff(self, staff):
        """Assign a staff member to this shift"""
        self.staff = staff
        self.is_open = False
        self.save(update_fields=['staff', 'is_open'])

    def mark_as_completed(self):
        """Mark the shift as completed"""
        self.status = 'completed'
        self.save(update_fields=['status'])

    def mark_as_missed(self):
        """Mark the shift as missed"""
        self.status = 'missed'
        self.save(update_fields=['status'])

class ShiftSwapRequest(models.Model):
    """Represents a request to swap shifts between staff members"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('cancelled', 'Cancelled'),
    )

    requested_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='requested_swaps')
    requested_shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='swap_requests')
    requested_to = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='received_swap_requests')
    offered_shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='offered_for_swap', null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_shift_swaps')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Swap request from {self.requested_by.user.get_full_name()} to {self.requested_to.user.get_full_name()}"

    def approve(self, manager=None):
        """Approve the swap request and update the shifts"""
        # Update the shifts
        temp_staff = self.requested_shift.staff

        if self.offered_shift:
            # Swap the staff members
            self.requested_shift.staff = self.requested_to
            self.offered_shift.staff = temp_staff
            self.offered_shift.save(update_fields=['staff'])
        else:
            # Just assign the requested shift to the other staff member
            self.requested_shift.staff = self.requested_to

        self.requested_shift.save(update_fields=['staff'])

        # Update the request status
        self.status = 'approved'
        self.responded_at = timezone.now()
        self.approved_by = manager
        self.save(update_fields=['status', 'responded_at', 'approved_by'])

    def deny(self, notes=None):
        """Deny the swap request"""
        self.status = 'denied'
        self.responded_at = timezone.now()
        if notes:
            self.notes = notes
        self.save(update_fields=['status', 'responded_at', 'notes'])

    def cancel(self):
        """Cancel the swap request"""
        self.status = 'cancelled'
        self.save(update_fields=['status'])

class ShiftTemplate(models.Model):
    """Represents a template for recurring shifts"""
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='shift_templates')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    staff = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='shift_templates')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        staff_name = self.staff.user.get_full_name() if self.staff else "Unassigned"
        return f"{self.position.title} - {self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')} - {staff_name}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

    def generate_shift(self, date):
        """Generate a shift from this template for a specific date"""
        # Ensure the date matches the day of week in the template
        if date.weekday() != self.day_of_week:
            raise ValidationError(f"Date {date} is not a {self.get_day_of_week_display()}")

        # Create datetime objects for start and end times
        start_datetime = timezone.make_aware(timezone.datetime.combine(date, self.start_time))
        end_datetime = timezone.make_aware(timezone.datetime.combine(date, self.end_time))

        # Create the shift
        shift = Shift.objects.create(
            position=self.position,
            start_time=start_datetime,
            end_time=end_datetime,
            staff=self.staff,
            notes=f"Generated from template: {self}",
            is_open=self.staff is None
        )

        return shift

class Schedule(models.Model):
    """Represents a schedule for a specific period"""
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("End date must be after or equal to start date")

    def publish(self):
        """Publish the schedule"""
        self.is_published = True
        self.save(update_fields=['is_published'])

    def unpublish(self):
        """Unpublish the schedule"""
        self.is_published = False
        self.save(update_fields=['is_published'])

    def get_shifts(self):
        """Get all shifts in this schedule period"""
        return Shift.objects.filter(
            start_time__date__gte=self.start_date,
            start_time__date__lte=self.end_date
        ).order_by('start_time')

    def generate_from_templates(self):
        """Generate shifts for this schedule period based on shift templates"""
        templates = ShiftTemplate.objects.filter(is_active=True)
        current_date = self.start_date
        shifts_created = 0

        while current_date <= self.end_date:
            day_templates = templates.filter(day_of_week=current_date.weekday())

            for template in day_templates:
                try:
                    template.generate_shift(current_date)
                    shifts_created += 1
                except ValidationError:
                    continue

            current_date += timezone.timedelta(days=1)

        return shifts_created

class ClockInOut(models.Model):
    """Represents a clock in/out record for a staff member"""
    TYPE_CHOICES = (
        ('in', 'Clock In'),
        ('out', 'Clock Out'),
        ('break_start', 'Break Start'),
        ('break_end', 'Break End'),
    )

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='clock_records')
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name='clock_records')
    record_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Clock In/Out Records"

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_record_type_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class PayrollPeriod(models.Model):
    """Represents a payroll period"""
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('processing', 'Processing'),
        ('closed', 'Closed'),
        ('paid', 'Paid'),
    )

    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payroll_periods')
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"Payroll Period: {self.start_date} to {self.end_date} ({self.get_status_display()})"

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("End date must be after or equal to start date")

    def close(self, user):
        """Close the payroll period"""
        self.status = 'closed'
        self.processed_by = user
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_by', 'processed_at'])

    def mark_as_paid(self, user):
        """Mark the payroll period as paid"""
        self.status = 'paid'
        self.processed_by = user
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_by', 'processed_at'])

class PayrollRecord(models.Model):
    """Represents a payroll record for a staff member in a payroll period"""
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='records')
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='payroll_records')
    regular_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    overtime_rate = models.DecimalField(max_digits=6, decimal_places=2)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('payroll_period', 'staff')

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.payroll_period}"

    def calculate_pay(self):
        """Calculate the gross and net pay"""
        # Calculate gross pay
        regular_pay = self.regular_hours * self.hourly_rate
        overtime_pay = self.overtime_hours * self.overtime_rate
        self.gross_pay = regular_pay + overtime_pay

        # Calculate net pay (gross pay minus deductions)
        self.net_pay = self.gross_pay - self.deductions

        self.save(update_fields=['gross_pay', 'net_pay'])
        return self.net_pay
