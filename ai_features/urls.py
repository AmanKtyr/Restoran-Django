from django.urls import path
from . import views

app_name = 'ai_features'

urlpatterns = [
    # AI Recommendation endpoints
    path('recommendations/', views.user_recommendations, name='user_recommendations'),
    path('recommendations/similar/<int:item_id>/', views.similar_items, name='similar_items'),
    path('recommendations/popular/', views.popular_recommendations, name='popular_recommendations'),
    
    # Chatbot endpoints
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('chatbot/api/message/', views.chatbot_message, name='chatbot_message'),
    path('chatbot/api/reset/', views.chatbot_reset, name='chatbot_reset'),
    
    # User preference endpoints
    path('preferences/', views.user_preferences, name='user_preferences'),
    path('preferences/update/', views.update_preferences, name='update_preferences'),
    
    # Food analysis endpoints
    path('food-analysis/<int:item_id>/', views.food_analysis, name='food_analysis'),
    
    # Voice ordering endpoints
    path('voice-order/', views.voice_order, name='voice_order'),
    
    # Interaction tracking endpoints
    path('track-interaction/', views.track_interaction, name='track_interaction'),
]
