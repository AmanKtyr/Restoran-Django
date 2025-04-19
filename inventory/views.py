from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.utils import timezone

from .models import (
    Supplier, Category, Unit, InventoryItem, SupplierItem,
    StockAdjustment, PurchaseOrder, PurchaseOrderItem,
    InventoryCheck, InventoryCheckItem
)

# Helper function to check if user is staff or admin
def is_staff_or_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_admin)
def inventory_dashboard(request):
    """Main inventory dashboard view"""
    # Get inventory statistics
    total_items = InventoryItem.objects.filter(is_active=True).count()
    low_stock_items = InventoryItem.objects.filter(
        is_active=True,
        current_stock__lte=F('minimum_stock')
    ).count()

    # Get recent purchase orders
    recent_orders = PurchaseOrder.objects.order_by('-created_at')[:5]

    # Get recent inventory checks
    recent_checks = InventoryCheck.objects.order_by('-created_at')[:5]

    context = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'recent_orders': recent_orders,
        'recent_checks': recent_checks,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def inventory_items(request):
    """View all inventory items"""
    items = InventoryItem.objects.all().order_by('name')
    categories = Category.objects.all()

    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        items = items.filter(category_id=category_id)

    # Filter by stock status if provided
    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        items = items.filter(current_stock__lte=F('minimum_stock'))
    elif stock_status == 'optimal':
        items = items.filter(
            current_stock__gt=F('minimum_stock'),
            current_stock__lte=F('optimal_stock')
        )
    elif stock_status == 'overstocked':
        items = items.filter(current_stock__gt=F('optimal_stock'))

    context = {
        'items': items,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': stock_status,
    }
    return render(request, 'inventory/items.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def inventory_item_detail(request, item_id):
    """View details of a specific inventory item"""
    item = get_object_or_404(InventoryItem, id=item_id)
    suppliers = item.suppliers.all()

    # Get stock adjustment history
    adjustments = StockAdjustment.objects.filter(item=item).order_by('-created_at')[:10]

    context = {
        'item': item,
        'suppliers': suppliers,
        'adjustments': adjustments,
    }
    return render(request, 'inventory/item_detail.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def suppliers(request):
    """View all suppliers"""
    suppliers_list = Supplier.objects.all().order_by('name')
    context = {
        'suppliers': suppliers_list,
    }
    return render(request, 'inventory/suppliers.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def supplier_detail(request, supplier_id):
    """View details of a specific supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    items = SupplierItem.objects.filter(supplier=supplier)

    # Get recent purchase orders from this supplier
    orders = PurchaseOrder.objects.filter(supplier=supplier).order_by('-created_at')[:5]

    context = {
        'supplier': supplier,
        'items': items,
        'orders': orders,
    }
    return render(request, 'inventory/supplier_detail.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def purchase_orders(request):
    """View all purchase orders"""
    orders = PurchaseOrder.objects.all().order_by('-created_at')

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    context = {
        'orders': orders,
        'selected_status': status,
    }
    return render(request, 'inventory/purchase_orders.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def purchase_order_detail(request, order_id):
    """View details of a specific purchase order"""
    order = get_object_or_404(PurchaseOrder, id=order_id)
    items = PurchaseOrderItem.objects.filter(purchase_order=order)

    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'inventory/purchase_order_detail.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def inventory_checks(request):
    """View all inventory checks"""
    checks = InventoryCheck.objects.all().order_by('-check_date')

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        checks = checks.filter(status=status)

    context = {
        'checks': checks,
        'selected_status': status,
    }
    return render(request, 'inventory/inventory_checks.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def inventory_check_detail(request, check_id):
    """View details of a specific inventory check"""
    check = get_object_or_404(InventoryCheck, id=check_id)
    items = InventoryCheckItem.objects.filter(inventory_check=check)

    context = {
        'check': check,
        'items': items,
    }
    return render(request, 'inventory/inventory_check_detail.html', context)
