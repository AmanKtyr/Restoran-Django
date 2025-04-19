from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class LoyaltyTier(models.Model):
    """Represents different loyalty program tiers"""
    name = models.CharField(max_length=50)
    points_threshold = models.PositiveIntegerField(help_text="Minimum points required to reach this tier")
    discount_percentage = models.PositiveIntegerField(help_text="Discount percentage for this tier")
    special_benefits = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    color = models.CharField(max_length=20, blank=True, help_text="Hex color code")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['points_threshold']

    def __str__(self):
        return f"{self.name} (Requires {self.points_threshold} points)"

class LoyaltyProgram(models.Model):
    """Represents the loyalty program settings"""
    name = models.CharField(max_length=100, default="Restaurant Rewards")
    description = models.TextField(blank=True)
    points_per_dollar = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                                         help_text="Points earned per dollar spent")
    points_expiration_months = models.PositiveIntegerField(default=12,
                                                       help_text="Number of months before points expire")
    is_active = models.BooleanField(default=True)
    terms_and_conditions = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Loyalty Program Settings"

class LoyaltyAccount(models.Model):
    """Represents a customer's loyalty account"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_account')
    points_balance = models.PositiveIntegerField(default=0)
    lifetime_points = models.PositiveIntegerField(default=0)
    tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    last_activity_date = models.DateTimeField(auto_now=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Loyalty Account"

    def update_tier(self):
        """Update the loyalty tier based on lifetime points"""
        eligible_tiers = LoyaltyTier.objects.filter(
            points_threshold__lte=self.lifetime_points,
            is_active=True
        ).order_by('-points_threshold')

        if eligible_tiers.exists():
            self.tier = eligible_tiers.first()
            self.save(update_fields=['tier'])

    def add_points(self, points, reason="Purchase"):
        """Add points to the account and create a transaction record"""
        self.points_balance += points
        self.lifetime_points += points
        self.save(update_fields=['points_balance', 'lifetime_points'])

        # Create transaction record
        LoyaltyTransaction.objects.create(
            account=self,
            points=points,
            transaction_type='earn',
            reason=reason
        )

        # Update tier if needed
        self.update_tier()

    def redeem_points(self, points, reason="Discount"):
        """Redeem points from the account and create a transaction record"""
        if points > self.points_balance:
            raise ValueError("Insufficient points balance")

        self.points_balance -= points
        self.save(update_fields=['points_balance'])

        # Create transaction record
        LoyaltyTransaction.objects.create(
            account=self,
            points=points,
            transaction_type='redeem',
            reason=reason
        )

class LoyaltyTransaction(models.Model):
    """Represents a loyalty points transaction"""
    TRANSACTION_TYPES = (
        ('earn', 'Earn'),
        ('redeem', 'Redeem'),
        ('expire', 'Expire'),
        ('adjust', 'Adjustment'),
    )

    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    points = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    reason = models.CharField(max_length=100)
    reference_id = models.CharField(max_length=100, blank=True, help_text="Order number, reservation ID, etc.")
    timestamp = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.points} points - {self.account.user.username}"

    def save(self, *args, **kwargs):
        # Set expiration date for earned points
        if self.transaction_type == 'earn' and not self.expiration_date:
            program = LoyaltyProgram.objects.first()
            if program:
                months = program.points_expiration_months
                self.expiration_date = timezone.now() + timezone.timedelta(days=30*months)

        super().save(*args, **kwargs)

class LoyaltyReward(models.Model):
    """Represents rewards that can be redeemed with loyalty points"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='loyalty_rewards/', blank=True, null=True)
    redemption_code = models.CharField(max_length=20, blank=True)
    limited_quantity = models.BooleanField(default=False)
    quantity_available = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['points_required']

    def __str__(self):
        return f"{self.name} ({self.points_required} points)"

    @property
    def is_available(self):
        now = timezone.now()
        date_valid = True

        if self.start_date and self.start_date > now:
            date_valid = False
        if self.end_date and self.end_date < now:
            date_valid = False

        quantity_valid = not self.limited_quantity or (self.quantity_available and self.quantity_available > 0)

        return self.is_active and date_valid and quantity_valid

class RewardRedemption(models.Model):
    """Represents a redemption of a loyalty reward"""
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='redemptions')
    reward = models.ForeignKey(LoyaltyReward, on_delete=models.CASCADE, related_name='redemptions')
    redemption_date = models.DateTimeField(auto_now_add=True)
    points_used = models.PositiveIntegerField()
    redemption_code = models.CharField(max_length=50, unique=True)
    is_used = models.BooleanField(default=False)
    used_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-redemption_date']

    def __str__(self):
        return f"{self.reward.name} redeemed by {self.account.user.username}"

    def mark_as_used(self):
        """Mark the redemption as used"""
        self.is_used = True
        self.used_date = timezone.now()
        self.save(update_fields=['is_used', 'used_date'])

@receiver(post_save, sender=User)
def create_loyalty_account(sender, instance, created, **kwargs):
    """Create a loyalty account when a new user is created"""
    if created:
        # Generate a unique referral code
        import uuid
        referral_code = str(uuid.uuid4())[:8].upper()

        # Create the loyalty account
        LoyaltyAccount.objects.create(
            user=instance,
            referral_code=referral_code
        )
