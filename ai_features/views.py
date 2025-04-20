import json
import uuid
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg
from django.utils import timezone

from menu.models import MenuItem, Category
from .models import (
    UserPreference, UserInteraction, AIRecommendation,
    AIFoodAnalysis, ChatbotConversation, ChatbotMessage, AISettings
)

# AI Recommendation Views

def user_recommendations(request):
    """Show personalized recommendations for the user"""
    # Get AI settings
    ai_settings = AISettings.get_settings()

    # Get menu items
    menu_items = MenuItem.objects.filter(is_active=True)

    # If user is authenticated, get personalized recommendations
    if request.user.is_authenticated:
        # Check if we have cached recommendations
        recommendations = AIRecommendation.objects.filter(
            user=request.user,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=ai_settings.cache_duration_minutes)
        ).select_related('menu_item').order_by('-score')[:8]

        # If no recommendations or cache expired, generate new ones
        if not recommendations:
            recommendations = generate_recommendations(request.user, menu_items)

        context = {
            'recommendations': recommendations,
            'is_personalized': True,
        }
    else:
        # For anonymous users, show popular items
        popular_items = menu_items.filter(is_popular=True)[:8]
        context = {
            'popular_items': popular_items,
            'is_personalized': False,
        }

    return render(request, 'ai_features/recommendations.html', context)

def similar_items(request, item_id):
    """Show items similar to the given item"""
    # Get the reference item
    reference_item = get_object_or_404(MenuItem, id=item_id, is_active=True)

    # Find similar items based on category and attributes
    similar_items = MenuItem.objects.filter(
        Q(category=reference_item.category) |
        Q(is_vegetarian=reference_item.is_vegetarian, is_vegan=reference_item.is_vegan) |
        Q(spice_level=reference_item.spice_level)
    ).exclude(id=reference_item.id).distinct()[:6]

    # Track this interaction
    if request.user.is_authenticated:
        UserInteraction.objects.create(
            user=request.user,
            menu_item=reference_item,
            interaction_type='view',
            interaction_data={'source': 'similar_items'}
        )

    context = {
        'reference_item': reference_item,
        'similar_items': similar_items,
    }

    return render(request, 'ai_features/similar_items.html', context)

def popular_recommendations(request):
    """Show popular items based on AI analysis"""
    # Get popular items with high presentation scores
    popular_items = MenuItem.objects.filter(is_popular=True, is_active=True)

    # If we have AI analysis data, use it to enhance recommendations
    analyzed_items = popular_items.filter(ai_analysis__isnull=False)
    if analyzed_items.exists():
        # Sort by presentation score
        popular_items = analyzed_items.order_by('-ai_analysis__presentation_score')[:8]
    else:
        popular_items = popular_items[:8]

    context = {
        'popular_items': popular_items,
    }

    return render(request, 'ai_features/popular_items.html', context)

# Helper function to generate recommendations
def generate_recommendations(user, menu_items, max_items=8):
    """Generate personalized recommendations for a user"""
    # Get user preferences if they exist
    try:
        preferences = UserPreference.objects.get(user=user)
        has_preferences = True
    except UserPreference.DoesNotExist:
        preferences = None
        has_preferences = False

    # Get user's past interactions
    interactions = UserInteraction.objects.filter(user=user)

    # Clear existing recommendations
    AIRecommendation.objects.filter(user=user).delete()

    recommendations = []

    # If user has preferences, use them
    if has_preferences:
        # Filter by dietary preferences
        filtered_items = menu_items
        if preferences.dietary_vegetarian:
            filtered_items = filtered_items.filter(is_vegetarian=True)
        if preferences.dietary_vegan:
            filtered_items = filtered_items.filter(is_vegan=True)
        if preferences.dietary_gluten_free:
            filtered_items = filtered_items.filter(is_gluten_free=True)

        # Consider spice preference
        spice_range = range(max(0, preferences.spice_preference - 1), min(4, preferences.spice_preference + 1) + 1)
        filtered_items = filtered_items.filter(spice_level__in=spice_range)

        # Consider favorite categories
        if preferences.favorite_categories.exists():
            category_items = filtered_items.filter(category__in=preferences.favorite_categories.all())
            if category_items.exists():
                filtered_items = category_items

        # Create recommendations with reasons
        for item in filtered_items[:max_items]:
            reason = get_recommendation_reason(item, preferences)
            rec = AIRecommendation.objects.create(
                user=user,
                menu_item=item,
                score=random.uniform(0.7, 1.0),  # In a real system, this would be a calculated score
                reason=reason,
                is_personalized=True
            )
            recommendations.append(rec)

    # If we don't have enough recommendations, add popular items
    if len(recommendations) < max_items:
        popular_items = menu_items.filter(is_popular=True).exclude(
            id__in=[rec.menu_item.id for rec in recommendations]
        )[:max_items - len(recommendations)]

        for item in popular_items:
            rec = AIRecommendation.objects.create(
                user=user,
                menu_item=item,
                score=random.uniform(0.5, 0.7),  # Lower score for non-personalized recommendations
                reason="This is one of our most popular items",
                is_personalized=False
            )
            recommendations.append(rec)

    return recommendations

def get_recommendation_reason(item, preferences):
    """Generate a personalized reason for recommending this item"""
    reasons = []

    # Dietary reasons
    if preferences.dietary_vegetarian and item.is_vegetarian:
        reasons.append("vegetarian")
    if preferences.dietary_vegan and item.is_vegan:
        reasons.append("vegan")
    if preferences.dietary_gluten_free and item.is_gluten_free:
        reasons.append("gluten-free")

    # Spice level
    if item.spice_level == preferences.spice_preference:
        reasons.append(f"has your preferred spice level ({item.get_spice_level_display()})")

    # Category preference
    if preferences.favorite_categories.filter(id=item.category.id).exists():
        reasons.append(f"from your favorite category ({item.category.name})")

    if reasons:
        return f"This item is {', '.join(reasons)}"
    else:
        return "This matches your taste preferences"

# Chatbot Views

def chatbot_view(request):
    """Show the chatbot interface"""
    # Get AI settings
    ai_settings = AISettings.get_settings()

    if not ai_settings.chatbot_enabled:
        return render(request, 'ai_features/chatbot_disabled.html')

    # Get or create a conversation
    if request.user.is_authenticated:
        conversation, created = ChatbotConversation.objects.get_or_create(
            user=request.user,
            is_active=True,
            defaults={'session_id': str(uuid.uuid4())}
        )
    else:
        # For anonymous users, use session ID
        if 'chatbot_session_id' not in request.session:
            request.session['chatbot_session_id'] = str(uuid.uuid4())

        session_id = request.session['chatbot_session_id']
        conversation, created = ChatbotConversation.objects.get_or_create(
            session_id=session_id,
            is_active=True,
            defaults={'user': None}
        )

    # If this is a new conversation, add the greeting message
    if created:
        ChatbotMessage.objects.create(
            conversation=conversation,
            message_type='bot',
            content=ai_settings.chatbot_greeting
        )

    # Get conversation messages
    messages = ChatbotMessage.objects.filter(conversation=conversation).order_by('timestamp')

    context = {
        'conversation': conversation,
        'messages': messages,
    }

    return render(request, 'ai_features/chatbot.html', context)

@csrf_exempt
@require_POST
def chatbot_message(request):
    """API endpoint to send a message to the chatbot"""
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()

        if not message_text:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        # Get or create conversation
        if request.user.is_authenticated:
            conversation = ChatbotConversation.objects.get(user=request.user, is_active=True)
        else:
            session_id = request.session.get('chatbot_session_id')
            if not session_id:
                return JsonResponse({'error': 'No active session'}, status=400)
            conversation = ChatbotConversation.objects.get(session_id=session_id, is_active=True)

        # Save user message
        user_message = ChatbotMessage.objects.create(
            conversation=conversation,
            message_type='user',
            content=message_text
        )

        # Process the message and generate a response
        response_text = process_chatbot_message(message_text, conversation, request.user)

        # Save bot response
        bot_message = ChatbotMessage.objects.create(
            conversation=conversation,
            message_type='bot',
            content=response_text
        )

        # Update conversation timestamp
        conversation.save()  # This updates last_updated

        return JsonResponse({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat(),
            },
            'bot_message': {
                'id': bot_message.id,
                'content': bot_message.content,
                'timestamp': bot_message.timestamp.isoformat(),
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def chatbot_reset(request):
    """Reset the chatbot conversation"""
    try:
        # Mark current conversation as inactive
        if request.user.is_authenticated:
            ChatbotConversation.objects.filter(user=request.user, is_active=True).update(is_active=False)
        else:
            session_id = request.session.get('chatbot_session_id')
            if session_id:
                ChatbotConversation.objects.filter(session_id=session_id, is_active=True).update(is_active=False)

        # Generate a new session ID for anonymous users
        if not request.user.is_authenticated:
            request.session['chatbot_session_id'] = str(uuid.uuid4())

        return JsonResponse({'success': True, 'message': 'Conversation reset successfully'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def process_chatbot_message(message, conversation, user):
    """Process a user message and generate a response"""
    # In a real implementation, this would use NLP and possibly call an external API
    # For now, we'll use a simple rule-based approach

    message_lower = message.lower()

    # Check for common intents
    if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! How can I assist you with our restaurant services today?"

    elif any(word in message_lower for word in ['menu', 'food', 'eat', 'dish', 'meal']):
        # Get some random menu items to recommend
        menu_items = MenuItem.objects.filter(is_active=True).order_by('?')[:3]
        if menu_items:
            items_text = ", ".join([f"{item.name} (₹{item.price})" for item in menu_items])
            return f"Here are some items from our menu you might enjoy: {items_text}. Would you like to see more options or get details about any of these dishes?"
        else:
            return "We have a variety of delicious dishes on our menu. You can view the full menu on our website or ask me about specific types of dishes."

    elif any(word in message_lower for word in ['book', 'reservation', 'table', 'booking']):
        return "You can book a table through our website's reservation system. Would you like me to guide you through the process or provide a direct link?"

    elif any(word in message_lower for word in ['hour', 'open', 'close', 'timing', 'schedule']):
        return "Our restaurant is open from 11:00 AM to 10:00 PM Monday through Thursday, and 11:00 AM to 11:00 PM Friday through Sunday."

    elif any(word in message_lower for word in ['location', 'address', 'where', 'place', 'direction']):
        return "We are located at 123 Main Street, Anytown. Would you like directions from your current location?"

    elif any(word in message_lower for word in ['vegetarian', 'vegan', 'gluten', 'allergy', 'dietary']):
        return "We offer a variety of vegetarian, vegan, and gluten-free options. All our menu items are clearly marked with dietary information. Is there a specific dietary requirement you're concerned about?"

    elif any(word in message_lower for word in ['recommend', 'suggestion', 'popular', 'best']):
        # Get popular items
        popular_items = MenuItem.objects.filter(is_active=True, is_popular=True).order_by('?')[:2]
        if popular_items:
            items_text = ", ".join([f"{item.name}" for item in popular_items])
            return f"Our most popular dishes include {items_text}. Would you like to know more about any of these?"
        else:
            return "I'd be happy to recommend some dishes! What kind of cuisine or flavors do you prefer?"

    elif any(word in message_lower for word in ['thanks', 'thank you', 'thx']):
        return "You're welcome! Is there anything else I can help you with?"

    elif any(word in message_lower for word in ['bye', 'goodbye', 'see you']):
        return "Thank you for chatting with us! Feel free to return if you have more questions. Have a great day!"

    else:
        # Default response
        return "I'm not sure I understand. Would you like to know about our menu, make a reservation, or learn about our location and hours?"

# User Preference Views

@login_required
def user_preferences(request):
    """Show and edit user preferences for AI recommendations"""
    # Get or create user preferences
    preferences, created = UserPreference.objects.get_or_create(user=request.user)

    # Get all categories for the form
    categories = Category.objects.filter(is_active=True)

    context = {
        'preferences': preferences,
        'categories': categories,
        'spice_levels': MenuItem.SPICE_LEVEL_CHOICES,
        'price_levels': [
            (1, 'Budget'),
            (2, 'Moderate'),
            (3, 'Premium')
        ]
    }

    return render(request, 'ai_features/user_preferences.html', context)

@login_required
@require_POST
def update_preferences(request):
    """Update user preferences"""
    # Get user preferences
    preferences, created = UserPreference.objects.get_or_create(user=request.user)

    # Update dietary preferences
    preferences.dietary_vegetarian = 'dietary_vegetarian' in request.POST
    preferences.dietary_vegan = 'dietary_vegan' in request.POST
    preferences.dietary_gluten_free = 'dietary_gluten_free' in request.POST

    # Update spice and price preferences
    preferences.spice_preference = int(request.POST.get('spice_preference', 2))
    preferences.price_sensitivity = int(request.POST.get('price_sensitivity', 2))

    # Save changes
    preferences.save()

    # Update favorite categories
    preferences.favorite_categories.clear()
    category_ids = request.POST.getlist('favorite_categories')
    if category_ids:
        categories = Category.objects.filter(id__in=category_ids)
        preferences.favorite_categories.add(*categories)

    # Clear existing recommendations to force regeneration
    AIRecommendation.objects.filter(user=request.user).delete()

    return redirect('ai_features:user_recommendations')

# Food Analysis Views

def food_analysis(request, item_id):
    """Show AI analysis of a food item"""
    # Get the menu item
    menu_item = get_object_or_404(MenuItem, id=item_id, is_active=True)

    # Get or create AI analysis
    try:
        analysis = AIFoodAnalysis.objects.get(menu_item=menu_item)
    except AIFoodAnalysis.DoesNotExist:
        # In a real implementation, this would call an AI service
        # For now, we'll create dummy data
        analysis = create_dummy_food_analysis(menu_item)

    context = {
        'menu_item': menu_item,
        'analysis': analysis,
    }

    return render(request, 'ai_features/food_analysis.html', context)

def create_dummy_food_analysis(menu_item):
    """Create dummy food analysis data for demonstration"""
    # Visual attributes that might be detected
    visual_attributes = {
        'colors': ['brown', 'green', 'red'] if random.random() > 0.5 else ['yellow', 'white', 'orange'],
        'textures': random.sample(['crispy', 'smooth', 'creamy', 'crunchy', 'juicy'], k=random.randint(1, 3)),
        'presentation': random.choice(['elegant', 'rustic', 'modern', 'traditional', 'artistic']),
        'garnishes': random.sample(['herbs', 'sauce drizzle', 'microgreens', 'edible flowers', 'citrus zest'], k=random.randint(0, 2)),
    }

    # Nutritional estimates
    nutritional_estimate = {
        'calories': random.randint(200, 800),
        'protein': random.randint(5, 30),
        'carbs': random.randint(10, 60),
        'fat': random.randint(5, 30),
        'fiber': random.randint(1, 10),
        'confidence': random.uniform(0.6, 0.9),
    }

    # Detected ingredients
    base_ingredients = ['salt', 'pepper', 'oil']
    possible_ingredients = [
        'chicken', 'beef', 'fish', 'tofu', 'rice', 'pasta', 'potato',
        'tomato', 'onion', 'garlic', 'cheese', 'cream', 'butter',
        'carrot', 'spinach', 'mushroom', 'bell pepper', 'broccoli',
        'lemon', 'lime', 'herbs', 'spices', 'flour', 'sugar'
    ]

    # Select some random ingredients
    selected_ingredients = random.sample(possible_ingredients, k=random.randint(3, 8))
    all_ingredients = base_ingredients + selected_ingredients

    ingredient_detection = {
        'ingredients': all_ingredients,
        'main_component': random.choice(selected_ingredients),
        'confidence': random.uniform(0.7, 0.95),
    }

    # Color palette
    color_palette = [
        {'color': '#8B4513', 'percentage': random.uniform(0.1, 0.4)},  # Brown
        {'color': '#228B22', 'percentage': random.uniform(0.1, 0.3)},  # Green
        {'color': '#CD5C5C', 'percentage': random.uniform(0.05, 0.2)},  # Red
        {'color': '#F5F5DC', 'percentage': random.uniform(0.1, 0.3)},  # Beige
        {'color': '#FFD700', 'percentage': random.uniform(0.05, 0.2)},  # Gold
    ]

    # Create and save the analysis
    analysis = AIFoodAnalysis.objects.create(
        menu_item=menu_item,
        visual_attributes=visual_attributes,
        nutritional_estimate=nutritional_estimate,
        ingredient_detection=ingredient_detection,
        presentation_score=random.uniform(7.0, 9.5),
        color_palette=color_palette
    )

    return analysis

# Voice Ordering View

def voice_order(request):
    """Voice-activated ordering interface"""
    # Get AI settings
    ai_settings = AISettings.get_settings()

    if not ai_settings.voice_recognition_enabled:
        return render(request, 'ai_features/voice_recognition_disabled.html')

    # Get menu categories and popular items for the interface
    categories = Category.objects.filter(is_active=True)
    popular_items = MenuItem.objects.filter(is_active=True, is_popular=True)[:6]

    context = {
        'categories': categories,
        'popular_items': popular_items,
        'voice_language': ai_settings.voice_recognition_language,
    }

    return render(request, 'ai_features/voice_order.html', context)

# Interaction Tracking

@csrf_exempt
@require_POST
def track_interaction(request):
    """Track user interactions with menu items for AI learning"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        interaction_type = data.get('interaction_type')
        interaction_data = data.get('interaction_data', {})

        if not item_id or not interaction_type:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Validate interaction type
        valid_types = [choice[0] for choice in UserInteraction.INTERACTION_TYPES]
        if interaction_type not in valid_types:
            return JsonResponse({'error': f'Invalid interaction type. Must be one of: {valid_types}'}, status=400)

        # Get the menu item
        try:
            menu_item = MenuItem.objects.get(id=item_id)
        except MenuItem.DoesNotExist:
            return JsonResponse({'error': 'Menu item not found'}, status=404)

        # Create the interaction record
        if request.user.is_authenticated:
            UserInteraction.objects.create(
                user=request.user,
                menu_item=menu_item,
                interaction_type=interaction_type,
                interaction_data=interaction_data
            )
            return JsonResponse({'success': True})
        else:
            # For anonymous users, we could track using session ID
            # but for simplicity, we'll just acknowledge the request
            return JsonResponse({'success': True, 'message': 'Interaction noted (anonymous user)'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
