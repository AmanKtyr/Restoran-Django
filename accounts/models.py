from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
import uuid
import datetime

class UserProfile(models.Model):
    # Basic profile information
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, help_text="Short bio about yourself")

    # Address information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Preferences
    DIETARY_CHOICES = (
        ('none', 'No Restrictions'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('gluten_free', 'Gluten Free'),
        ('dairy_free', 'Dairy Free'),
        ('nut_free', 'Nut Free'),
        ('halal', 'Halal'),
        ('kosher', 'Kosher'),
    )
    dietary_preference = models.CharField(max_length=20, choices=DIETARY_CHOICES, default='none')
    food_allergies = models.TextField(blank=True, help_text="List any food allergies you have")
    spice_preference = models.IntegerField(default=2, choices=[(1, 'Mild'), (2, 'Medium'), (3, 'Spicy'), (4, 'Very Spicy')])
    favorite_cuisine = models.CharField(max_length=100, blank=True)

    # Communication preferences
    is_subscribed_to_newsletter = models.BooleanField(default=False)
    receive_order_updates = models.BooleanField(default=True, help_text="Receive updates about your orders")
    receive_promotional_emails = models.BooleanField(default=True, help_text="Receive promotional emails and offers")
    receive_sms_notifications = models.BooleanField(default=False, help_text="Receive SMS notifications")

    # Social media profiles
    facebook_profile = models.URLField(blank=True)
    instagram_profile = models.URLField(blank=True)
    twitter_profile = models.URLField(blank=True)

    # Loyalty and account info
    loyalty_points = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True, help_text="Your unique referral code")
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Generate a referral code if one doesn't exist
        if not self.referral_code:
            self.referral_code = generate_referral_code()
        super().save(*args, **kwargs)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except User.profile.RelatedObjectDoesNotExist:
        # Create a profile if it doesn't exist
        UserProfile.objects.create(user=instance)

def generate_referral_code():
    """Generate a unique referral code"""
    return uuid.uuid4().hex[:8].upper()


class UserAddress(models.Model):
    """Model for storing multiple user addresses"""
    ADDRESS_TYPES = (
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='home')
    name = models.CharField(max_length=100, help_text="Name this address (e.g. Home, Office)")
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=17, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Address'
        verbose_name_plural = 'User Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.username}'s {self.get_address_type_display()} Address"

    def save(self, *args, **kwargs):
        # If this address is being set as default, unset any other default addresses
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class UserFavorite(models.Model):
    """Model for storing user favorites"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.CharField(max_length=20, choices=(
        ('menu_item', 'Menu Item'),
        ('category', 'Category'),
    ))
    object_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Favorite'
        verbose_name_plural = 'User Favorites'
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s favorite {self.content_type}"


class EmailVerificationToken(models.Model):
    """Model for storing email verification tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Email verification token for {self.user.username}"

    def is_valid(self):
        """Check if the token is valid (not expired and not used)"""
        return not self.is_used and self.expires_at > timezone.now()

    @classmethod
    def generate_token(cls, user, expiry_hours=24):
        """Generate a new verification token for a user"""
        # Invalidate any existing tokens
        cls.objects.filter(user=user, is_used=False).update(is_used=True)

        # Generate a new token
        token = uuid.uuid4().hex
        expires_at = timezone.now() + datetime.timedelta(hours=expiry_hours)

        # Create and return the token
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

    def get_verification_url(self, request=None):
        """Get the full verification URL"""
        path = reverse('accounts:verify_email', kwargs={'token': self.token})
        if request:
            return request.build_absolute_uri(path)
        return f"{settings.SITE_URL}{path}"


class ReferralBonus(models.Model):
    """Model for tracking referral bonuses"""
    BONUS_TYPES = (
        ('points', 'Loyalty Points'),
        ('discount', 'Discount'),
        ('free_item', 'Free Item'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )

    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_bonuses_given')
    referred = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_bonuses_received')
    bonus_type = models.CharField(max_length=20, choices=BONUS_TYPES)
    bonus_value = models.DecimalField(max_digits=10, decimal_places=2, help_text='Value of the bonus (points, discount amount, etc.)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Referral Bonus'
        verbose_name_plural = 'Referral Bonuses'
        ordering = ['-created_at']

    def __str__(self):
        return f"Referral bonus from {self.referrer.username} to {self.referred.username}"

    def is_valid(self):
        """Check if the bonus is valid (not expired and pending/approved)"""
        if self.status not in ['pending', 'approved']:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False
        return True

    def redeem(self):
        """Mark the bonus as redeemed"""
        if not self.is_valid():
            return False

        self.status = 'approved'
        self.redeemed_at = timezone.now()
        self.save(update_fields=['status', 'redeemed_at'])

        # Apply the bonus based on type
        if self.bonus_type == 'points':
            # Add loyalty points to the referred user
            profile = self.referred.profile
            profile.loyalty_points += int(self.bonus_value)
            profile.save(update_fields=['loyalty_points'])

        return True


class UserActivity(models.Model):
    """Model to track user activities"""
    ACTIVITY_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('register', 'Registration'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('order', 'Order Placed'),
        ('booking', 'Booking Made'),
        ('review', 'Review Posted'),
        ('favorite', 'Item Favorited'),
        ('loyalty', 'Loyalty Activity'),
        ('address_added', 'Address Added'),
        ('address_updated', 'Address Updated'),
        ('address_removed', 'Address Removed'),
        ('email_verified', 'Email Verified'),
        ('two_factor_enabled', 'Two-Factor Authentication Enabled'),
        ('two_factor_disabled', 'Two-Factor Authentication Disabled'),
        ('email_verification_sent', 'Email Verification Sent'),
        ('referral_created', 'Referral Created'),
        ('referral_completed', 'Referral Completed'),
        ('referral_bonus_earned', 'Referral Bonus Earned'),
        ('referral_bonus_redeemed', 'Referral Bonus Redeemed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(null=True, blank=True, help_text='Additional data related to the activity')

    class Meta:
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def log_activity(cls, user, activity_type, description, request=None, metadata=None):
        """Helper method to log user activity"""
        ip_address = None
        user_agent = ''

        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Create activity log
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
