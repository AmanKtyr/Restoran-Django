from django.contrib import admin
from .models import TeamMember, Testimonial, ContactMessage, Service, RestaurantSettings

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'position', 'bio')
    list_editable = ('display_order', 'is_active')

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'rating', 'is_active')
    list_filter = ('rating', 'is_active')
    search_fields = ('name', 'position', 'content')
    list_editable = ('is_active',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('is_read',)
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')

    def has_add_permission(self, request):
        return False

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    list_editable = ('display_order', 'is_active')

@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('General Settings', {
            'fields': ('site_title', 'site_description', 'timezone', 'currency', 'currency_symbol', 'tax_rate')
        }),
        ('Restaurant Information', {
            'fields': ('restaurant_name', 'restaurant_logo', 'restaurant_address', 'restaurant_phone',
                      'restaurant_email', 'opening_hours', 'google_maps_embed')
        }),
        ('Appearance Settings', {
            'fields': ('primary_color', 'secondary_color', 'font_family', 'hero_image', 'favicon')
        }),
        ('Email Settings', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
                      'email_from_name', 'email_from_address')
        }),
        ('Payment Settings', {
            'fields': ('enable_stripe', 'stripe_public_key', 'stripe_secret_key',
                      'enable_paypal', 'paypal_client_id', 'paypal_secret_key')
        }),
        ('Social Media Settings', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 'youtube_url')
        }),
        ('SEO Settings', {
            'fields': ('meta_keywords', 'meta_description', 'google_analytics_id')
        }),
        ('Backup Settings', {
            'fields': ('enable_scheduled_backups', 'backup_frequency', 'backup_retention_days')
        }),
        ('System Settings', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
    )

    def has_add_permission(self, request):
        # Only allow one settings object
        return not RestaurantSettings.objects.exists()
