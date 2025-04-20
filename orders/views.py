from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Cart, CartItem, Order, OrderItem
from menu.models import MenuItem

@login_required
def cart_view(request):
    # Get or create cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)

    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
    }
    return render(request, 'orders/cart.html', context)

@login_required
def add_to_cart(request, menu_item_id):
    if request.method == 'POST':
        menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))
        special_instructions = request.POST.get('special_instructions', '')

        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Check if item already exists in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            menu_item=menu_item,
            defaults={
                'quantity': quantity,
                'special_instructions': special_instructions
            }
        )

        # If item already exists, update quantity
        if not item_created:
            cart_item.quantity += quantity
            cart_item.special_instructions = special_instructions
            cart_item.save()

        messages.success(request, f"{menu_item.name} added to your cart.")

        # If AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"{menu_item.name} added to your cart.",
                'cart_total': cart.get_total_items()
            })

        # Otherwise redirect to referring page or menu
        return redirect(request.META.get('HTTP_REFERER', 'menu:menu_list'))

    # If not POST, redirect to menu
    return redirect('menu:menu_list')

@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        action = request.POST.get('action')

        if action == 'remove':
            cart_item.delete()
            messages.success(request, "Item removed from cart.")
        elif action == 'update':
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.special_instructions = request.POST.get('special_instructions', '')
                cart_item.save()
                messages.success(request, "Cart updated.")
            else:
                cart_item.delete()
                messages.success(request, "Item removed from cart.")

        # If AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart = cart_item.cart
            return JsonResponse({
                'status': 'success',
                'cart_total': cart.get_total_items(),
                'cart_total_price': float(cart.get_total_price())
            })

        return redirect('orders:cart')

    return redirect('orders:cart')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    # Check if cart is empty
    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty. Add some items before checkout.")
        return redirect('menu:menu_list')

    # Calculate order totals
    subtotal = cart.get_total_price()
    tax_rate = Decimal('0.10')  # 10% tax
    tax = subtotal * tax_rate
    delivery_fee = Decimal('5.00') if request.session.get('order_type') == 'delivery' else Decimal('0.00')
    total = subtotal + tax + delivery_fee

    if request.method == 'POST':
        # Process the order
        with transaction.atomic():
            # Create order
            # Get form data
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address', '')
            city = request.POST.get('city', '')
            state = request.POST.get('state', '')
            postal_code = request.POST.get('postal_code', '')
            order_type = request.POST.get('order_type', 'delivery')
            payment_method = request.POST.get('payment_method', 'cash')
            special_instructions = request.POST.get('special_instructions', '')

            # Create order with the correct field names
            order = Order.objects.create(
                user=request.user,
                name=full_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                zip_code=postal_code,
                order_type=order_type,
                payment_method=payment_method,
                special_request=special_instructions,  # Map special_instructions to special_request
                subtotal=subtotal,
                tax=tax,
                delivery_fee=delivery_fee,
                discount_amount=Decimal('0.00'),
                total=total,
                estimated_delivery_time=timezone.now() + timezone.timedelta(minutes=45)
            )

            # Create order items from cart items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    quantity=cart_item.quantity,
                    price=cart_item.menu_item.price,
                    special_instructions=cart_item.special_instructions
                )

            # Clear the cart
            cart.items.all().delete()

            messages.success(request, f"Order #{order.order_number} placed successfully!")
            return redirect('orders:order_confirmation', order_id=order.id)

    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
        'subtotal': subtotal,
        'tax': tax,
        'delivery_fee': delivery_fee,
        'total': total,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'orders/order_confirmation.html', context)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_history.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'orders/order_detail.html', context)

def order_tracker(request):
    """View for tracking order status"""
    order_number = request.GET.get('order_number')
    error_message = None
    order = None

    if order_number:
        # Try to find the order
        order = Order.objects.filter(order_number=order_number).first()

        if not order:
            error_message = "We couldn't find an order with that number. Please check and try again."

    context = {
        'order': order,
        'error_message': error_message
    }

    return render(request, 'orders/order_tracker.html', context)
