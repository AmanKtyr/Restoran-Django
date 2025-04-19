from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from .models import KitchenStation, OrderItemStatus, KitchenLog, KitchenAlert
from orders.models import Order, OrderItem

# Helper function to check if user is kitchen staff
def is_kitchen_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or user.groups.filter(name='Kitchen Staff').exists())

@login_required
@user_passes_test(is_kitchen_staff)
def kitchen_dashboard(request):
    """Main kitchen dashboard view"""
    # Get active stations
    stations = KitchenStation.objects.filter(is_active=True).order_by('display_order')

    # Get active alerts
    alerts = KitchenAlert.objects.filter(
        Q(is_active=True) &
        (Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
    )

    # Get pending and in-progress orders
    active_orders = Order.objects.filter(
        status__in=['confirmed', 'preparing']
    ).order_by('priority', 'created_at')

    # Get order items with their kitchen status
    order_items_status = OrderItemStatus.objects.filter(
        order_item__order__in=active_orders,
        status__in=['pending', 'in_progress']
    ).select_related(
        'order_item__menu_item', 'order_item__order', 'station', 'assigned_to'
    )

    # Group order items by station
    station_items = {}
    for station in stations:
        station_items[station] = order_items_status.filter(station=station)

    # Get unassigned items
    unassigned_items = order_items_status.filter(station__isnull=True)

    context = {
        'stations': stations,
        'alerts': alerts,
        'active_orders': active_orders,
        'station_items': station_items,
        'unassigned_items': unassigned_items,
    }

    return render(request, 'kitchen/dashboard.html', context)

@login_required
@user_passes_test(is_kitchen_staff)
def station_view(request, station_id):
    """View for a specific kitchen station"""
    station = get_object_or_404(KitchenStation, id=station_id, is_active=True)

    # Get active alerts for this station
    alerts = KitchenAlert.objects.filter(
        Q(is_active=True) &
        (Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())) &
        (Q(stations=station) | Q(stations__isnull=True))
    ).distinct()

    # Get order items for this station
    order_items_status = OrderItemStatus.objects.filter(
        station=station,
        status__in=['pending', 'in_progress']
    ).select_related(
        'order_item__menu_item', 'order_item__order', 'assigned_to'
    ).order_by(
        'order_item__order__priority',
        'order_item__order__created_at',
        'status'
    )

    context = {
        'station': station,
        'alerts': alerts,
        'order_items_status': order_items_status,
    }

    return render(request, 'kitchen/station.html', context)

@login_required
@user_passes_test(is_kitchen_staff)
def order_detail(request, order_id):
    """Detailed view of a specific order"""
    order = get_object_or_404(Order, id=order_id)

    # Get all order items with their kitchen status
    order_items = OrderItem.objects.filter(order=order).select_related('menu_item')

    # Get kitchen status for each order item
    for item in order_items:
        try:
            item.kitchen_status_obj = OrderItemStatus.objects.get(order_item=item)
        except OrderItemStatus.DoesNotExist:
            item.kitchen_status_obj = None

    # Get kitchen logs for this order
    logs = KitchenLog.objects.filter(order=order).order_by('-timestamp')

    context = {
        'order': order,
        'order_items': order_items,
        'logs': logs,
    }

    return render(request, 'kitchen/order_detail.html', context)

@login_required
@user_passes_test(is_kitchen_staff)
def update_order_item_status(request, item_status_id):
    """Update the status of an order item"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    item_status = get_object_or_404(OrderItemStatus, id=item_status_id)
    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    if new_status not in dict(OrderItemStatus.STATUS_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid status'})

    # Update the status
    old_status = item_status.status
    item_status.status = new_status
    item_status.notes = notes
    item_status.save()

    # Create a log entry
    KitchenLog.objects.create(
        order=item_status.order_item.order,
        order_item=item_status.order_item,
        station=item_status.station,
        user=request.user,
        event_type='status_change',
        event_description=f"Status changed from {old_status} to {new_status}. {notes}"
    )

    return JsonResponse({
        'success': True,
        'status': new_status,
        'status_display': item_status.get_status_display(),
        'started_at': item_status.started_at.isoformat() if item_status.started_at else None,
        'completed_at': item_status.completed_at.isoformat() if item_status.completed_at else None,
    })

@login_required
@user_passes_test(is_kitchen_staff)
def assign_order_item(request, item_status_id):
    """Assign an order item to a station and/or user"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    item_status = get_object_or_404(OrderItemStatus, id=item_status_id)
    station_id = request.POST.get('station_id')
    user_id = request.POST.get('user_id')

    # Update the assignment
    if station_id:
        station = get_object_or_404(KitchenStation, id=station_id)
        item_status.station = station

    if user_id:
        from django.contrib.auth.models import User
        user = get_object_or_404(User, id=user_id)
        item_status.assigned_to = user

    item_status.save()

    # Create a log entry
    assignment_details = []
    if station_id:
        assignment_details.append(f"Station: {item_status.station.name}")
    if user_id:
        assignment_details.append(f"User: {item_status.assigned_to.get_full_name() or item_status.assigned_to.username}")

    KitchenLog.objects.create(
        order=item_status.order_item.order,
        order_item=item_status.order_item,
        station=item_status.station,
        user=request.user,
        event_type='assignment',
        event_description=f"Item assigned to {', '.join(assignment_details)}"
    )

    return JsonResponse({
        'success': True,
        'station': item_status.station.name if item_status.station else None,
        'assigned_to': item_status.assigned_to.get_full_name() if item_status.assigned_to else None,
    })

@login_required
@user_passes_test(is_kitchen_staff)
def create_alert(request):
    """Create a new kitchen alert"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    title = request.POST.get('title')
    message = request.POST.get('message')
    priority = request.POST.get('priority', 'medium')
    station_ids = request.POST.getlist('station_ids')
    expires_in_hours = request.POST.get('expires_in_hours')

    if not title or not message:
        return JsonResponse({'success': False, 'error': 'Title and message are required'})

    # Create the alert
    alert = KitchenAlert.objects.create(
        title=title,
        message=message,
        priority=priority,
        created_by=request.user,
    )

    # Set expiration time if provided
    if expires_in_hours:
        try:
            hours = int(expires_in_hours)
            alert.expires_at = timezone.now() + timezone.timedelta(hours=hours)
            alert.save()
        except ValueError:
            pass

    # Add stations if provided
    if station_ids:
        stations = KitchenStation.objects.filter(id__in=station_ids)
        alert.stations.add(*stations)

    return JsonResponse({
        'success': True,
        'alert_id': alert.id,
        'title': alert.title,
        'priority': alert.priority,
    })

@login_required
@user_passes_test(is_kitchen_staff)
def dismiss_alert(request, alert_id):
    """Dismiss a kitchen alert"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    alert = get_object_or_404(KitchenAlert, id=alert_id)
    alert.is_active = False
    alert.save()

    return JsonResponse({'success': True})

@login_required
@user_passes_test(is_kitchen_staff)
def get_order_updates(request):
    """API endpoint to get updates on orders (for AJAX polling)"""
    # Get the timestamp of the last update from the client
    last_update = request.GET.get('last_update')
    if last_update:
        try:
            last_update = timezone.datetime.fromisoformat(last_update)
        except ValueError:
            last_update = None

    # If no valid timestamp provided, use current time minus 5 minutes
    if not last_update:
        last_update = timezone.now() - timezone.timedelta(minutes=5)

    # Get new or updated orders
    updated_orders = Order.objects.filter(
        Q(created_at__gt=last_update) | Q(updated_at__gt=last_update),
        status__in=['confirmed', 'preparing', 'ready']
    ).values('id', 'order_number', 'status', 'created_at', 'updated_at')

    # Get new or updated order item statuses
    updated_statuses = OrderItemStatus.objects.filter(
        Q(order_item__order__created_at__gt=last_update) |
        Q(order_item__order__updated_at__gt=last_update) |
        Q(started_at__gt=last_update) |
        Q(completed_at__gt=last_update)
    ).select_related('order_item__order', 'order_item__menu_item').values(
        'id', 'status', 'started_at', 'completed_at',
        'order_item__id', 'order_item__menu_item__name', 'order_item__order__id'
    )

    # Get new alerts
    new_alerts = KitchenAlert.objects.filter(
        Q(created_at__gt=last_update) &
        Q(is_active=True) &
        (Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
    ).values('id', 'title', 'message', 'priority', 'created_at')

    return JsonResponse({
        'success': True,
        'timestamp': timezone.now().isoformat(),
        'updated_orders': list(updated_orders),
        'updated_statuses': list(updated_statuses),
        'new_alerts': list(new_alerts),
    })
