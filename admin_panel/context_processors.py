from core.models import ContactMessage

def admin_notifications(request):
    """
    Context processor to add notification counts to all admin panel templates
    """
    context = {
        'unread_messages': 0,
        'low_stock_items': 0,
    }
    
    # Only add these for authenticated staff/admin users
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        # Get unread messages count
        context['unread_messages'] = ContactMessage.objects.filter(is_read=False).count()
        
        # Get low stock items count
        try:
            from inventory.models import InventoryItem
            from django.db.models import F
            context['low_stock_items'] = InventoryItem.objects.filter(
                is_active=True,
                current_stock__lte=F('minimum_stock')
            ).count()
        except (ImportError, Exception):
            pass
    
    return context
