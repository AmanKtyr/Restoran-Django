from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import OrderItem, Order
from .models import OrderItemStatus, KitchenLog, MenuItemStation

@receiver(post_save, sender=OrderItem)
def create_order_item_status(sender, instance, created, **kwargs):
    """Create an OrderItemStatus when a new OrderItem is created"""
    if created:
        # Check if the order is in a state that requires kitchen tracking
        if instance.order.status in ['confirmed', 'preparing']:
            # Try to find a station for this menu item
            station = None
            try:
                menu_item_station = MenuItemStation.objects.filter(menu_item=instance.menu_item).first()
                if menu_item_station:
                    station = menu_item_station.station
            except Exception:
                pass
            
            # Create the status object
            status = OrderItemStatus.objects.create(
                order_item=instance,
                station=station
            )
            
            # Create a log entry
            KitchenLog.objects.create(
                order=instance.order,
                order_item=instance,
                station=station,
                event_type='status_change',
                event_description=f"Item added to kitchen queue: {instance.menu_item.name} (Qty: {instance.quantity})"
            )

@receiver(post_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """Handle order status changes"""
    # Skip if this is a new order
    if instance._state.adding:
        return
    
    # Check if the order status has changed to 'confirmed'
    if instance.status == 'confirmed':
        # Create OrderItemStatus for all items in this order that don't have one yet
        for order_item in instance.items.all():
            if not hasattr(order_item, 'kitchen_status'):
                # Try to find a station for this menu item
                station = None
                try:
                    menu_item_station = MenuItemStation.objects.filter(menu_item=order_item.menu_item).first()
                    if menu_item_station:
                        station = menu_item_station.station
                except Exception:
                    pass
                
                # Create the status object
                status = OrderItemStatus.objects.create(
                    order_item=order_item,
                    station=station
                )
                
                # Create a log entry
                KitchenLog.objects.create(
                    order=instance,
                    order_item=order_item,
                    station=station,
                    event_type='status_change',
                    event_description=f"Item added to kitchen queue: {order_item.menu_item.name} (Qty: {order_item.quantity})"
                )
        
        # Create a log entry for the order confirmation
        KitchenLog.objects.create(
            order=instance,
            event_type='status_change',
            event_description=f"Order confirmed and sent to kitchen"
        )
