from django.db import models
from django.conf import settings
from menu.models import MenuItem, Category

class UserPreference(models.Model):
    """Stores user preferences for AI recommendations"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_preferences')
    favorite_categories = models.ManyToManyField(Category, blank=True, related_name='user_favorites')
    dietary_vegetarian = models.BooleanField(default=False)
    dietary_vegan = models.BooleanField(default=False)
    dietary_gluten_free = models.BooleanField(default=False)
    spice_preference = models.IntegerField(default=2, choices=MenuItem.SPICE_LEVEL_CHOICES)
    price_sensitivity = models.IntegerField(default=2, choices=[
        (1, 'Budget'),
        (2, 'Moderate'),
        (3, 'Premium')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Preferences"

class UserInteraction(models.Model):
    """Tracks user interactions with menu items for AI learning"""
    INTERACTION_TYPES = [
        ('view', 'Viewed'),
        ('order', 'Ordered'),
        ('favorite', 'Favorited'),
        ('review', 'Reviewed'),
        ('recommend_click', 'Clicked Recommendation'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_interactions')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='user_interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    interaction_data = models.JSONField(blank=True, null=True, help_text="Additional data about the interaction")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['menu_item', 'interaction_type']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.get_interaction_type_display()} {self.menu_item.name}"

class AIRecommendation(models.Model):
    """Stores AI-generated recommendations for users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_recommendations')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='ai_recommendations')
    score = models.FloatField(help_text="Recommendation score between 0 and 1")
    reason = models.CharField(max_length=255, help_text="Reason for recommendation")
    is_personalized = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'menu_item')
        ordering = ['-score']

    def __str__(self):
        return f"Recommendation: {self.menu_item.name} for {self.user.username}"

class AIFoodAnalysis(models.Model):
    """Stores AI analysis of food images"""
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='ai_analysis')
    visual_attributes = models.JSONField(help_text="Visual attributes detected by AI")
    nutritional_estimate = models.JSONField(blank=True, null=True, help_text="AI-estimated nutritional information")
    ingredient_detection = models.JSONField(blank=True, null=True, help_text="AI-detected ingredients")
    presentation_score = models.FloatField(default=0.0, help_text="AI score for food presentation (0-10)")
    color_palette = models.JSONField(blank=True, null=True, help_text="Dominant colors in the food")
    last_analyzed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Analysis for {self.menu_item.name}"

class ChatbotConversation(models.Model):
    """Stores chatbot conversations with users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chatbot_conversations', null=True, blank=True)
    session_id = models.CharField(max_length=100, help_text="Session ID for anonymous users")
    conversation_data = models.JSONField(default=list, help_text="Full conversation history")
    started_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        if self.user:
            return f"Conversation with {self.user.username}"
        return f"Anonymous conversation {self.session_id}"

class ChatbotMessage(models.Model):
    """Individual messages in a chatbot conversation"""
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('bot', 'Bot Message'),
        ('system', 'System Message'),
    ]

    conversation = models.ForeignKey(ChatbotConversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    intent = models.CharField(max_length=100, blank=True, help_text="Detected intent of user message")
    entities = models.JSONField(blank=True, null=True, help_text="Entities extracted from message")

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}"

class AISettings(models.Model):
    """Global settings for AI features"""
    # Recommendation Engine Settings
    recommendation_algorithm = models.CharField(max_length=50, default="collaborative_filtering", choices=[
        ("collaborative_filtering", "Collaborative Filtering"),
        ("content_based", "Content-Based Filtering"),
        ("hybrid", "Hybrid Approach"),
    ])
    recommendation_freshness_weight = models.FloatField(default=0.3, help_text="Weight for new items (0-1)")
    recommendation_diversity_weight = models.FloatField(default=0.2, help_text="Weight for diversity (0-1)")

    # Chatbot Settings
    chatbot_enabled = models.BooleanField(default=True)
    chatbot_greeting = models.TextField(default="Hello! I'm your restaurant assistant. How can I help you today?")
    chatbot_model = models.CharField(max_length=50, default="gpt-3.5-turbo", help_text="Model used for chatbot")

    # Image Analysis Settings
    image_analysis_enabled = models.BooleanField(default=True)
    image_analysis_confidence_threshold = models.FloatField(default=0.7, help_text="Minimum confidence for image analysis results")

    # Voice Recognition Settings
    voice_recognition_enabled = models.BooleanField(default=False)
    voice_recognition_language = models.CharField(max_length=10, default="en-US")

    # API Keys and Integration Settings
    openai_api_key = models.CharField(max_length=255, blank=True, help_text="API key for OpenAI services")
    google_vision_api_key = models.CharField(max_length=255, blank=True, help_text="API key for Google Vision")

    # Performance Settings
    cache_recommendations = models.BooleanField(default=True)
    cache_duration_minutes = models.IntegerField(default=60)

    # Usage Limits
    daily_api_request_limit = models.IntegerField(default=1000)
    max_conversation_length = models.IntegerField(default=20, help_text="Maximum messages in a conversation")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AI Settings'
        verbose_name_plural = 'AI Settings'

    def __str__(self):
        return "AI Feature Settings"

    @classmethod
    def get_settings(cls):
        """Get the settings object, creating it if it doesn't exist"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
