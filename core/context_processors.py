from core.models import RestaurantSettings

def restaurant_settings(request):
    """
    Context processor to add restaurant settings to all templates
    """
    settings = RestaurantSettings.get_settings()
    return {
        'currency_symbol': settings.currency_symbol,
        'restaurant_settings': settings,
    }
