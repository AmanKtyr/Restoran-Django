from django.contrib import admin
from .models import (
    UserPreference, UserInteraction, AIRecommendation,
    AIFoodAnalysis, ChatbotConversation, ChatbotMessage, AISettings
)

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'dietary_vegetarian', 'dietary_vegan', 'dietary_gluten_free', 'spice_preference', 'price_sensitivity')
    list_filter = ('dietary_vegetarian', 'dietary_vegan', 'dietary_gluten_free', 'spice_preference', 'price_sensitivity')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('favorite_categories',)

@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu_item', 'interaction_type', 'timestamp')
    list_filter = ('interaction_type', 'timestamp')
    search_fields = ('user__username', 'menu_item__name')
    date_hierarchy = 'timestamp'

@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu_item', 'score', 'reason', 'is_personalized', 'created_at')
    list_filter = ('is_personalized', 'created_at')
    search_fields = ('user__username', 'menu_item__name', 'reason')
    date_hierarchy = 'created_at'

@admin.register(AIFoodAnalysis)
class AIFoodAnalysisAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'presentation_score', 'last_analyzed')
    list_filter = ('last_analyzed',)
    search_fields = ('menu_item__name',)
    date_hierarchy = 'last_analyzed'

class ChatbotMessageInline(admin.TabularInline):
    model = ChatbotMessage
    extra = 0
    readonly_fields = ('timestamp',)

@admin.register(ChatbotConversation)
class ChatbotConversationAdmin(admin.ModelAdmin):
    list_display = ('get_user_display', 'session_id', 'started_at', 'last_updated', 'is_active')
    list_filter = ('is_active', 'started_at', 'last_updated')
    search_fields = ('user__username', 'session_id')
    date_hierarchy = 'started_at'
    inlines = [ChatbotMessageInline]

    def get_user_display(self, obj):
        return obj.user.username if obj.user else f"Anonymous ({obj.session_id})"
    get_user_display.short_description = 'User'

@admin.register(ChatbotMessage)
class ChatbotMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'message_type', 'content_preview', 'intent', 'timestamp')
    list_filter = ('message_type', 'timestamp')
    search_fields = ('content', 'intent')
    date_hierarchy = 'timestamp'

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Recommendation Engine', {
            'fields': ('recommendation_algorithm', 'recommendation_freshness_weight', 'recommendation_diversity_weight')
        }),
        ('Chatbot Settings', {
            'fields': ('chatbot_enabled', 'chatbot_greeting', 'chatbot_model')
        }),
        ('Image Analysis', {
            'fields': ('image_analysis_enabled', 'image_analysis_confidence_threshold')
        }),
        ('Voice Recognition', {
            'fields': ('voice_recognition_enabled', 'voice_recognition_language')
        }),
        ('API Keys', {
            'fields': ('openai_api_key', 'google_vision_api_key'),
            'classes': ('collapse',),
        }),
        ('Performance', {
            'fields': ('cache_recommendations', 'cache_duration_minutes')
        }),
        ('Usage Limits', {
            'fields': ('daily_api_request_limit', 'max_conversation_length')
        }),
    )

    def has_add_permission(self, request):
        # Only allow one settings object
        return not AISettings.objects.exists()
