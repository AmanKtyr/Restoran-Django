from django.db import models
from django.core.exceptions import ValidationError

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='team/')
    facebook_link = models.URLField(blank=True)
    twitter_link = models.URLField(blank=True)
    instagram_link = models.URLField(blank=True)
    linkedin_link = models.URLField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.name} - {self.position}"

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    rating = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.rating} stars"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"

class Service(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, help_text="Font Awesome class (e.g., 'fa-utensils')")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title

class RestaurantSettings(models.Model):
    """Global settings for the restaurant"""
    # General Settings
    site_title = models.CharField(max_length=100, default="Restaurant Name")
    site_description = models.TextField(blank=True, help_text="A brief description of your restaurant")
    timezone = models.CharField(max_length=50, default="UTC")
    currency = models.CharField(max_length=10, default="USD")
    currency_symbol = models.CharField(max_length=5, default="$")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Tax rate as a decimal (e.g., 0.08 for 8%)")

    # Restaurant Information
    restaurant_name = models.CharField(max_length=100, default="Restaurant Name")
    restaurant_logo = models.ImageField(upload_to='settings/', blank=True, null=True)
    restaurant_address = models.TextField(blank=True)
    restaurant_phone = models.CharField(max_length=20, blank=True)
    restaurant_email = models.EmailField(blank=True)
    opening_hours = models.TextField(blank=True, help_text="Format: Day: HH:MM AM/PM - HH:MM AM/PM")
    google_maps_embed = models.TextField(blank=True, help_text="Google Maps embed code")

    # Appearance Settings
    primary_color = models.CharField(max_length=7, default="#FEA116", help_text="Hex color code")
    secondary_color = models.CharField(max_length=7, default="#0F172B", help_text="Hex color code")
    font_family = models.CharField(max_length=50, default="Nunito")
    hero_image = models.ImageField(upload_to='settings/', blank=True, null=True)
    favicon = models.ImageField(upload_to='settings/', blank=True, null=True)

    # Email Settings
    smtp_host = models.CharField(max_length=100, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.CharField(max_length=100, blank=True)
    smtp_password = models.CharField(max_length=100, blank=True)
    email_from_name = models.CharField(max_length=100, blank=True)
    email_from_address = models.EmailField(blank=True)

    # Payment Settings
    enable_stripe = models.BooleanField(default=False)
    stripe_public_key = models.CharField(max_length=100, blank=True)
    stripe_secret_key = models.CharField(max_length=100, blank=True)
    enable_paypal = models.BooleanField(default=False)
    paypal_client_id = models.CharField(max_length=100, blank=True)
    paypal_secret_key = models.CharField(max_length=100, blank=True)

    # Social Media Settings
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # SEO Settings
    meta_keywords = models.TextField(blank=True, help_text="Comma-separated keywords for SEO")
    meta_description = models.TextField(blank=True, help_text="Meta description for SEO")
    google_analytics_id = models.CharField(max_length=50, blank=True, help_text="Google Analytics tracking ID")

    # Backup Settings
    enable_scheduled_backups = models.BooleanField(default=False)
    backup_frequency = models.CharField(max_length=20, default="daily", choices=[
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ])
    backup_retention_days = models.PositiveIntegerField(default=30, help_text="Number of days to keep backups")

    # System Settings
    maintenance_mode = models.BooleanField(default=False, help_text="Put the site in maintenance mode")
    maintenance_message = models.TextField(blank=True, default="We are currently performing maintenance. Please check back soon.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Restaurant Settings'
        verbose_name_plural = 'Restaurant Settings'

    def __str__(self):
        return "Restaurant Settings"

    def clean(self):
        # Ensure only one instance of settings exists
        if RestaurantSettings.objects.exists() and not self.pk:
            raise ValidationError("There can only be one Restaurant Settings instance")
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get the settings instance, creating it if it doesn't exist"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
