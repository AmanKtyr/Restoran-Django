from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Avg, F, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from menu.models import Category, MenuItem
from booking.models import Booking, BookingSettings
from orders.models import Order, OrderItem
from reviews.models import Review
from core.models import TeamMember, Testimonial, ContactMessage, Service, RestaurantSettings
from analytics.models import MarketingCampaign, CampaignPerformance

# Import models from other apps
try:
    from inventory.models import InventoryItem, PurchaseOrder, InventoryCheck
except ImportError:
    pass

try:
    from kitchen.models import KitchenStation, OrderItemStatus, KitchenAlert
except ImportError:
    pass

try:
    from staffing.models import StaffProfile, Department, Position, Shift, TimeOffRequest
except ImportError:
    pass

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# Helper function to check if models are available
def is_app_installed(app_name):
    from django.apps import apps
    return apps.is_installed(app_name)

# Admin authentication views
def admin_login(request):
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('admin_panel:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and is_admin(user):
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('admin_panel:dashboard')
        else:
            messages.error(request, 'Invalid username or password, or insufficient permissions.')

    return render(request, 'admin_panel/login.html')

@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_panel:login')

# Dashboard view
@login_required
@user_passes_test(is_admin)
def dashboard(request):
    # Get statistics for dashboard
    today = timezone.now().date()
    month_start = today.replace(day=1)
    last_30_days = today - timedelta(days=30)

    # Order statistics
    total_orders = Order.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    monthly_orders = Order.objects.filter(created_at__date__gte=month_start).count()
    monthly_revenue = Order.objects.filter(created_at__date__gte=month_start).aggregate(Sum('total'))['total__sum'] or 0

    # Booking statistics
    total_bookings = Booking.objects.count()
    recent_bookings = Booking.objects.order_by('-created_at')[:5]
    pending_bookings = Booking.objects.filter(status='pending').count()

    # User statistics
    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__date__gte=last_30_days).count()

    # Menu statistics
    total_menu_items = MenuItem.objects.count()
    popular_items = MenuItem.objects.filter(is_popular=True).count()

    # Review statistics
    total_reviews = Review.objects.count()
    avg_rating = Review.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    recent_reviews = Review.objects.order_by('-created_at')[:5]

    # Message statistics
    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    recent_messages = ContactMessage.objects.order_by('-created_at')[:5]

    # Inventory statistics
    try:
        from inventory.models import InventoryItem
        from django.db.models import F
        low_stock_items = InventoryItem.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock')
        ).count()
    except (ImportError, Exception):
        low_stock_items = 0

    context = {
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'monthly_orders': monthly_orders,
        'monthly_revenue': monthly_revenue,
        'total_bookings': total_bookings,
        'recent_bookings': recent_bookings,
        'pending_bookings': pending_bookings,
        'total_users': total_users,
        'new_users': new_users,
        'total_menu_items': total_menu_items,
        'popular_items': popular_items,
        'total_reviews': total_reviews,
        'avg_rating': avg_rating,
        'recent_reviews': recent_reviews,
        'unread_messages': unread_messages,
        'recent_messages': recent_messages,
        'low_stock_items': low_stock_items,
        'today': today,
    }

    return render(request, 'admin_panel/dashboard.html', context)

# Menu management views
@login_required
@user_passes_test(is_admin)
def menu_list(request):
    categories = Category.objects.all()
    menu_items = MenuItem.objects.all()
    context = {
        'categories': categories,
        'menu_items': menu_items,
    }
    return render(request, 'admin_panel/menu/menu_list.html', context)

@login_required
@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'admin_panel/menu/category_list.html', {'categories': categories})

@login_required
@user_passes_test(is_admin)
def category_add(request):
    # Implementation will be added later
    return render(request, 'admin_panel/menu/category_form.html')

@login_required
@user_passes_test(is_admin)
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    return render(request, 'admin_panel/menu/category_form.html', {'category': category})

@login_required
@user_passes_test(is_admin)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, 'Category deleted successfully!')
    return redirect('admin_panel:category_list')

@login_required
@user_passes_test(is_admin)
def menu_item_list(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'admin_panel/menu/menu_item_list.html', {'menu_items': menu_items})

@login_required
@user_passes_test(is_admin)
def menu_item_add(request):
    # Implementation will be added later
    return render(request, 'admin_panel/menu/menu_item_form.html')

@login_required
@user_passes_test(is_admin)
def menu_item_edit(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    return render(request, 'admin_panel/menu/menu_item_form.html', {'menu_item': menu_item})

@login_required
@user_passes_test(is_admin)
def menu_item_delete(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    menu_item.delete()
    messages.success(request, 'Menu item deleted successfully!')
    return redirect('admin_panel:menu_item_list')

# Booking management views
@login_required
@user_passes_test(is_admin)
def booking_list(request):
    bookings = Booking.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/booking/booking_list.html', {'bookings': bookings})

@login_required
@user_passes_test(is_admin)
def booking_add(request):
    if request.method == 'POST':
        # Process form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        guests = request.POST.get('guests')
        date = request.POST.get('date')
        time = request.POST.get('time')
        special_request = request.POST.get('special_request')
        status = request.POST.get('status')

        # Combine date and time
        from datetime import datetime
        date_time_str = f"{date} {time}"
        date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")

        # Create booking
        Booking.objects.create(
            name=name,
            email=email,
            phone=phone,
            guests=guests,
            date_time=date_time,
            special_request=special_request,
            status=status
        )

        messages.success(request, 'Booking created successfully!')
        return redirect('admin_panel:booking_list')

    return render(request, 'admin_panel/booking/booking_form.html')

@login_required
@user_passes_test(is_admin)
def booking_edit(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if request.method == 'POST':
        # Process form data
        booking.name = request.POST.get('name')
        booking.email = request.POST.get('email')
        booking.phone = request.POST.get('phone')
        booking.guests = request.POST.get('guests')
        date = request.POST.get('date')
        time = request.POST.get('time')
        booking.special_request = request.POST.get('special_request')
        booking.status = request.POST.get('status')

        # Combine date and time
        from datetime import datetime
        date_time_str = f"{date} {time}"
        booking.date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")

        # Save booking
        booking.save()

        messages.success(request, 'Booking updated successfully!')
        return redirect('admin_panel:booking_list')

    return render(request, 'admin_panel/booking/booking_form.html', {'booking': booking})

@login_required
@user_passes_test(is_admin)
def booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    booking.delete()
    messages.success(request, 'Booking deleted successfully!')
    return redirect('admin_panel:booking_list')

# User management views
@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_panel/user/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_add(request):
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        phone = request.POST.get('phone')

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser
        )

        # Update profile
        if hasattr(user, 'profile'):
            user.profile.phone = phone
            if 'profile_picture' in request.FILES:
                user.profile.profile_picture = request.FILES['profile_picture']
            user.profile.save()

        messages.success(request, f'User {username} created successfully!')
        return redirect('admin_panel:user_list')

    return render(request, 'admin_panel/user/user_form.html')

@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        phone = request.POST.get('phone')

        # Update user
        user_obj.email = email
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.is_active = is_active
        user_obj.is_staff = is_staff
        user_obj.is_superuser = is_superuser

        # Update password if provided
        if password:
            user_obj.set_password(password)

        user_obj.save()

        # Update profile
        if hasattr(user_obj, 'profile'):
            user_obj.profile.phone = phone
            if 'profile_picture' in request.FILES:
                user_obj.profile.profile_picture = request.FILES['profile_picture']
            user_obj.profile.save()

        messages.success(request, f'User {user_obj.username} updated successfully!')
        return redirect('admin_panel:user_list')

    return render(request, 'admin_panel/user/user_form.html', {'user_obj': user_obj})

@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    username = user_obj.username

    # Don't allow deleting yourself
    if user_obj == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('admin_panel:user_list')

    user_obj.delete()
    messages.success(request, f'User {username} deleted successfully!')
    return redirect('admin_panel:user_list')

# Order management views
@login_required
@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/order/order_list.html', {'orders': orders})

@login_required
@user_passes_test(is_admin)
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'admin_panel/order/order_detail.html', {'order': order})

@login_required
@user_passes_test(is_admin)
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        # Update order status and payment status
        order.status = request.POST.get('status')
        order.payment_status = request.POST.get('payment_status')

        # Update other fields if they exist in the form
        if 'payment_method' in request.POST:
            order.payment_method = request.POST.get('payment_method')

        if 'order_type' in request.POST:
            order.order_type = request.POST.get('order_type')

        if 'notes' in request.POST:
            order.notes = request.POST.get('notes')

        # Customer information
        if 'name' in request.POST:
            order.name = request.POST.get('name')

        if 'email' in request.POST:
            order.email = request.POST.get('email')

        if 'phone' in request.POST:
            order.phone = request.POST.get('phone')

        # Delivery information
        if order.order_type == 'delivery':
            order.address = request.POST.get('address', '')
            order.address_line2 = request.POST.get('address_line2', '')
            order.city = request.POST.get('city', '')
            order.state = request.POST.get('state', '')
            order.zip_code = request.POST.get('zip_code', '')
            order.delivery_fee = Decimal(request.POST.get('delivery_fee', 0))

        # Pricing information
        if 'tax' in request.POST:
            order.tax = Decimal(request.POST.get('tax', 0))

        if 'discount_amount' in request.POST:
            order.discount_amount = Decimal(request.POST.get('discount_amount', 0))

        if 'coupon_code' in request.POST:
            order.coupon_code = request.POST.get('coupon_code', '')

        # Recalculate total
        subtotal = order.get_subtotal()
        order.total = subtotal + order.tax + order.delivery_fee - order.discount_amount

        order.save()

        messages.success(request, f'Order #{order.order_number} updated successfully!')

        # Redirect based on where the form was submitted from
        if 'status' in request.POST and 'payment_status' in request.POST and len(request.POST) <= 3:
            # If only status and payment_status were updated (from order detail page)
            return redirect('admin_panel:order_detail', pk=order.id)
        else:
            # If full form was submitted
            return redirect('admin_panel:order_list')

    return render(request, 'admin_panel/order/order_form.html', {'order': order})

# Review management views
@login_required
@user_passes_test(is_admin)
def review_list(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/review/review_list.html', {'reviews': reviews})

@login_required
@user_passes_test(is_admin)
def review_detail(request, pk):
    review = get_object_or_404(Review, pk=pk)
    return render(request, 'admin_panel/review/review_detail.html', {'review': review})

@login_required
@user_passes_test(is_admin)
def review_edit(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action', 'edit')

        if action == 'reply':
            # Update reply
            review.reply = request.POST.get('reply')
            from django.utils import timezone
            review.reply_date = timezone.now()
            review.save()
            messages.success(request, 'Reply updated successfully!')
            return redirect('admin_panel:review_detail', pk=review.id)

        elif action == 'status':
            # Update status
            review.is_approved = request.POST.get('is_approved') == '1'
            review.is_featured = request.POST.get('is_featured') == '1'
            review.save()
            messages.success(request, 'Review status updated successfully!')
            return redirect('admin_panel:review_detail', pk=review.id)

        else:  # action == 'edit'
            # Update review content
            review.title = request.POST.get('title')
            review.rating = int(request.POST.get('rating'))
            review.content = request.POST.get('content')
            review.is_approved = 'is_approved' in request.POST
            review.is_featured = 'is_featured' in request.POST

            if request.POST.get('reply'):
                review.reply = request.POST.get('reply')
                if not review.reply_date:
                    from django.utils import timezone
                    review.reply_date = timezone.now()

            review.save()
            messages.success(request, 'Review updated successfully!')
            return redirect('admin_panel:review_list')

    return render(request, 'admin_panel/review/review_form.html', {'review': review})

@login_required
@user_passes_test(is_admin)
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, 'Review deleted successfully!')
    return redirect('admin_panel:review_list')

# Team management views
@login_required
@user_passes_test(is_admin)
def team_list(request):
    team_members = TeamMember.objects.all().order_by('display_order')
    return render(request, 'admin_panel/team/team_list.html', {'team_members': team_members})

@login_required
@user_passes_test(is_admin)
def team_add(request):
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        position = request.POST.get('position')
        bio = request.POST.get('bio')
        display_order = request.POST.get('display_order')
        is_active = 'is_active' in request.POST
        facebook_url = request.POST.get('facebook_url')
        twitter_url = request.POST.get('twitter_url')
        instagram_url = request.POST.get('instagram_url')
        linkedin_url = request.POST.get('linkedin_url')

        # Create team member
        team_member = TeamMember.objects.create(
            name=name,
            position=position,
            bio=bio,
            display_order=display_order,
            is_active=is_active,
            facebook_url=facebook_url,
            twitter_url=twitter_url,
            instagram_url=instagram_url,
            linkedin_url=linkedin_url
        )

        # Handle image upload
        if 'image' in request.FILES:
            team_member.image = request.FILES['image']
            team_member.save()

        messages.success(request, 'Team member added successfully!')
        return redirect('admin_panel:team_list')

    return render(request, 'admin_panel/team/team_form.html')

@login_required
@user_passes_test(is_admin)
def team_edit(request, pk):
    team_member = get_object_or_404(TeamMember, pk=pk)

    if request.method == 'POST':
        # Get form data
        team_member.name = request.POST.get('name')
        team_member.position = request.POST.get('position')
        team_member.bio = request.POST.get('bio')
        team_member.display_order = request.POST.get('display_order')
        team_member.is_active = 'is_active' in request.POST
        team_member.facebook_url = request.POST.get('facebook_url')
        team_member.twitter_url = request.POST.get('twitter_url')
        team_member.instagram_url = request.POST.get('instagram_url')
        team_member.linkedin_url = request.POST.get('linkedin_url')

        # Handle image upload
        if 'image' in request.FILES:
            team_member.image = request.FILES['image']

        # Handle image deletion
        if 'delete_image' in request.POST and team_member.image:
            team_member.image.delete()
            team_member.image = None

        team_member.save()
        messages.success(request, 'Team member updated successfully!')
        return redirect('admin_panel:team_list')

    return render(request, 'admin_panel/team/team_form.html', {'team_member': team_member})

@login_required
@user_passes_test(is_admin)
def team_delete(request, pk):
    team_member = get_object_or_404(TeamMember, pk=pk)
    team_member.delete()
    messages.success(request, 'Team member deleted successfully!')
    return redirect('admin_panel:team_list')

# Testimonial management views
@login_required
@user_passes_test(is_admin)
def testimonial_list(request):
    testimonials = Testimonial.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/testimonial/testimonial_list.html', {'testimonials': testimonials})

@login_required
@user_passes_test(is_admin)
def testimonial_add(request):
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        position = request.POST.get('position')
        content = request.POST.get('content')
        rating = int(request.POST.get('rating', 5))
        is_active = 'is_active' in request.POST

        # Create testimonial
        testimonial = Testimonial.objects.create(
            name=name,
            position=position,
            content=content,
            rating=rating,
            is_active=is_active
        )

        # Handle image upload
        if 'image' in request.FILES:
            testimonial.image = request.FILES['image']
            testimonial.save()

        messages.success(request, 'Testimonial added successfully!')
        return redirect('admin_panel:testimonial_list')

    return render(request, 'admin_panel/testimonial/testimonial_form.html')

@login_required
@user_passes_test(is_admin)
def testimonial_edit(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)

    if request.method == 'POST':
        # Get form data
        testimonial.name = request.POST.get('name')
        testimonial.position = request.POST.get('position')
        testimonial.content = request.POST.get('content')
        testimonial.rating = int(request.POST.get('rating', 5))
        testimonial.is_active = 'is_active' in request.POST

        # Handle image upload
        if 'image' in request.FILES:
            testimonial.image = request.FILES['image']

        # Handle image deletion
        if 'delete_image' in request.POST and testimonial.image:
            testimonial.image.delete()
            testimonial.image = None

        testimonial.save()
        messages.success(request, 'Testimonial updated successfully!')
        return redirect('admin_panel:testimonial_list')

    return render(request, 'admin_panel/testimonial/testimonial_form.html', {'testimonial': testimonial})

@login_required
@user_passes_test(is_admin)
def testimonial_delete(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonial.delete()
    messages.success(request, 'Testimonial deleted successfully!')
    return redirect('admin_panel:testimonial_list')

# Service management views
@login_required
@user_passes_test(is_admin)
def service_list(request):
    services = Service.objects.all().order_by('display_order')
    return render(request, 'admin_panel/service/service_list.html', {'services': services})

@login_required
@user_passes_test(is_admin)
def service_add(request):
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        icon_class = request.POST.get('icon_class')
        display_order = request.POST.get('display_order')
        is_active = 'is_active' in request.POST

        # Create service
        Service.objects.create(
            title=title,
            description=description,
            icon_class=icon_class,
            display_order=display_order,
            is_active=is_active
        )

        messages.success(request, 'Service added successfully!')
        return redirect('admin_panel:service_list')

    return render(request, 'admin_panel/service/service_form.html')

@login_required
@user_passes_test(is_admin)
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        # Get form data
        service.title = request.POST.get('title')
        service.description = request.POST.get('description')
        service.icon_class = request.POST.get('icon_class')
        service.display_order = request.POST.get('display_order')
        service.is_active = 'is_active' in request.POST

        service.save()
        messages.success(request, 'Service updated successfully!')
        return redirect('admin_panel:service_list')

    return render(request, 'admin_panel/service/service_form.html', {'service': service})

@login_required
@user_passes_test(is_admin)
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    messages.success(request, 'Service deleted successfully!')
    return redirect('admin_panel:service_list')

# Contact message management views
@login_required
@user_passes_test(is_admin)
def message_list(request):
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/message/message_list.html', {'messages': messages_list})

@login_required
@user_passes_test(is_admin)
def message_detail(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    # Mark as read when viewed
    if not message.is_read:
        message.is_read = True
        from django.utils import timezone
        message.read_at = timezone.now()
        message.save()
    return render(request, 'admin_panel/message/message_detail.html', {'message': message})

@login_required
@user_passes_test(is_admin)
def message_delete(request, pk):
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    contact_message.delete()
    messages.success(request, 'Message deleted successfully!')
    return redirect('admin_panel:message_list')

# Settings view
@login_required
@user_passes_test(is_admin)
def settings(request):
    # Get or create settings
    settings_obj = RestaurantSettings.get_settings()

    # Get or create booking settings
    booking_settings, created = BookingSettings.objects.get_or_create(id=1)

    if request.method == 'POST':
        # Determine which settings section is being updated
        section = request.POST.get('section', 'general')

        if section == 'general':
            # Update general settings
            settings_obj.site_title = request.POST.get('site_title')
            settings_obj.site_description = request.POST.get('site_description')
            settings_obj.timezone = request.POST.get('timezone')
            settings_obj.currency = request.POST.get('currency')
            settings_obj.currency_symbol = request.POST.get('currency_symbol')
            settings_obj.tax_rate = request.POST.get('tax_rate')

        elif section == 'restaurant':
            # Update restaurant information
            settings_obj.restaurant_name = request.POST.get('restaurant_name')
            settings_obj.restaurant_address = request.POST.get('restaurant_address')
            settings_obj.restaurant_phone = request.POST.get('restaurant_phone')
            settings_obj.restaurant_email = request.POST.get('restaurant_email')
            settings_obj.opening_hours = request.POST.get('opening_hours')
            settings_obj.google_maps_embed = request.POST.get('google_maps_embed')

            # Handle logo upload
            if 'restaurant_logo' in request.FILES:
                settings_obj.restaurant_logo = request.FILES['restaurant_logo']

        elif section == 'appearance':
            # Update appearance settings
            settings_obj.primary_color = request.POST.get('primary_color')
            settings_obj.secondary_color = request.POST.get('secondary_color')
            settings_obj.font_family = request.POST.get('font_family')

            # Handle image uploads
            if 'hero_image' in request.FILES:
                settings_obj.hero_image = request.FILES['hero_image']

            if 'favicon' in request.FILES:
                settings_obj.favicon = request.FILES['favicon']

        elif section == 'email':
            # Update email settings
            settings_obj.smtp_host = request.POST.get('smtp_host')
            settings_obj.smtp_port = request.POST.get('smtp_port')
            settings_obj.smtp_username = request.POST.get('smtp_username')
            settings_obj.smtp_password = request.POST.get('smtp_password')
            settings_obj.email_from_name = request.POST.get('email_from_name')
            settings_obj.email_from_address = request.POST.get('email_from_address')

        elif section == 'payment':
            # Update payment settings
            settings_obj.enable_stripe = 'enable_stripe' in request.POST
            settings_obj.stripe_public_key = request.POST.get('stripe_public_key')
            settings_obj.stripe_secret_key = request.POST.get('stripe_secret_key')
            settings_obj.enable_paypal = 'enable_paypal' in request.POST
            settings_obj.paypal_client_id = request.POST.get('paypal_client_id')
            settings_obj.paypal_secret_key = request.POST.get('paypal_secret_key')

        elif section == 'social':
            # Update social media settings
            settings_obj.facebook_url = request.POST.get('facebook_url')
            settings_obj.twitter_url = request.POST.get('twitter_url')
            settings_obj.instagram_url = request.POST.get('instagram_url')
            settings_obj.linkedin_url = request.POST.get('linkedin_url')
            settings_obj.youtube_url = request.POST.get('youtube_url')

        elif section == 'seo':
            # Update SEO settings
            settings_obj.meta_keywords = request.POST.get('meta_keywords')
            settings_obj.meta_description = request.POST.get('meta_description')
            settings_obj.google_analytics_id = request.POST.get('google_analytics_id')

        elif section == 'backup':
            # Update backup settings
            settings_obj.enable_scheduled_backups = 'enable_scheduled_backups' in request.POST
            settings_obj.backup_frequency = request.POST.get('backup_frequency')
            settings_obj.backup_retention_days = request.POST.get('backup_retention_days')

        elif section == 'system':
            # Update system settings
            settings_obj.maintenance_mode = 'maintenance_mode' in request.POST
            settings_obj.maintenance_message = request.POST.get('maintenance_message')

        elif section == 'booking':
            # Update booking settings
            booking_settings.min_booking_notice_hours = request.POST.get('min_booking_notice_hours')
            booking_settings.max_booking_days_ahead = request.POST.get('max_booking_days_ahead')
            booking_settings.default_booking_duration_mins = request.POST.get('default_booking_duration_mins')
            booking_settings.auto_confirm_bookings = 'auto_confirm_bookings' in request.POST
            booking_settings.send_confirmation_emails = 'send_confirmation_emails' in request.POST
            booking_settings.send_reminder_emails = 'send_reminder_emails' in request.POST
            booking_settings.reminder_hours_before = request.POST.get('reminder_hours_before')
            booking_settings.max_party_size = request.POST.get('max_party_size')
            booking_settings.min_party_size = request.POST.get('min_party_size')
            booking_settings.allow_online_cancellation = 'allow_online_cancellation' in request.POST
            booking_settings.cancellation_deadline_hours = request.POST.get('cancellation_deadline_hours')
            booking_settings.require_deposit = 'require_deposit' in request.POST
            booking_settings.deposit_amount = request.POST.get('deposit_amount')
            booking_settings.deposit_percentage = request.POST.get('deposit_percentage')

            # Save booking settings
            booking_settings.save()

        # Save settings
        settings_obj.save()

        messages.success(request, 'Settings updated successfully!')
        return redirect('admin_panel:settings')

    return render(request, 'admin_panel/settings.html', {'settings': settings_obj, 'booking_settings': booking_settings})

# Marketing campaign views
@login_required
@user_passes_test(is_admin)
def campaign_list(request):
    campaigns = MarketingCampaign.objects.all().order_by('-start_date')
    return render(request, 'admin_panel/marketing/campaign_list.html', {'campaigns': campaigns})

@login_required
@user_passes_test(is_admin)
def campaign_add(request):
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        budget = request.POST.get('budget')
        target_audience = request.POST.get('target_audience')
        promotion_code = request.POST.get('promotion_code')
        discount_percentage = request.POST.get('discount_percentage')
        is_active = 'is_active' in request.POST

        # Create campaign
        campaign = MarketingCampaign.objects.create(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            target_audience=target_audience,
            promotion_code=promotion_code,
            discount_percentage=discount_percentage,
            is_active=is_active,
            created_by=request.user
        )

        messages.success(request, 'Marketing campaign created successfully!')
        return redirect('admin_panel:campaign_detail', pk=campaign.id)

    return render(request, 'admin_panel/marketing/campaign_form.html')

@login_required
@user_passes_test(is_admin)
def campaign_detail(request, pk):
    campaign = get_object_or_404(MarketingCampaign, pk=pk)
    today = timezone.now().date().isoformat()

    # Calculate campaign duration
    campaign_duration = (campaign.end_date - campaign.start_date).days + 1

    # Get performance metrics
    performances = CampaignPerformance.objects.filter(campaign=campaign).order_by('-date')

    # Calculate totals and averages
    total_impressions = performances.aggregate(Sum('impressions'))['impressions__sum'] or 0
    total_clicks = performances.aggregate(Sum('clicks'))['clicks__sum'] or 0
    total_conversions = performances.aggregate(Sum('conversions'))['conversions__sum'] or 0
    total_revenue = performances.aggregate(Sum('revenue'))['revenue__sum'] or 0
    total_cost = performances.aggregate(Sum('cost'))['cost__sum'] or 0

    # Calculate derived metrics
    conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    average_roi = performances.aggregate(Avg('roi'))['roi__avg'] or 0

    context = {
        'campaign': campaign,
        'today': today,
        'campaign_duration': campaign_duration,
        'performances': performances,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'total_conversions': total_conversions,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'conversion_rate': round(conversion_rate, 2),
        'average_roi': round(average_roi, 2),
    }

    return render(request, 'admin_panel/marketing/campaign_detail.html', context)

@login_required
@user_passes_test(is_admin)
def campaign_edit(request, pk):
    campaign = get_object_or_404(MarketingCampaign, pk=pk)

    if request.method == 'POST':
        # Get form data
        campaign.name = request.POST.get('name')
        campaign.description = request.POST.get('description')
        campaign.start_date = request.POST.get('start_date')
        campaign.end_date = request.POST.get('end_date')
        campaign.budget = request.POST.get('budget')
        campaign.target_audience = request.POST.get('target_audience')
        campaign.promotion_code = request.POST.get('promotion_code')
        campaign.discount_percentage = request.POST.get('discount_percentage')
        campaign.is_active = 'is_active' in request.POST

        campaign.save()
        messages.success(request, 'Marketing campaign updated successfully!')
        return redirect('admin_panel:campaign_detail', pk=campaign.id)

    return render(request, 'admin_panel/marketing/campaign_form.html', {'campaign': campaign})

@login_required
@user_passes_test(is_admin)
def campaign_delete(request, pk):
    campaign = get_object_or_404(MarketingCampaign, pk=pk)
    campaign.delete()
    messages.success(request, 'Marketing campaign deleted successfully!')
    return redirect('admin_panel:campaign_list')

@login_required
@user_passes_test(is_admin)
def add_campaign_performance(request, pk):
    campaign = get_object_or_404(MarketingCampaign, pk=pk)

    if request.method == 'POST':
        # Get form data
        date = request.POST.get('date')
        impressions = int(request.POST.get('impressions'))
        clicks = int(request.POST.get('clicks'))
        conversions = int(request.POST.get('conversions'))
        revenue = Decimal(request.POST.get('revenue'))
        cost = Decimal(request.POST.get('cost'))

        # Create performance record
        performance = CampaignPerformance.objects.create(
            campaign=campaign,
            date=date,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            revenue=revenue,
            cost=cost
        )

        messages.success(request, 'Performance data added successfully!')
        return redirect('admin_panel:campaign_detail', pk=campaign.id)

    return redirect('admin_panel:campaign_detail', pk=campaign.id)

# Staff & Operations views
@login_required
@user_passes_test(is_admin)
def staffing_dashboard(request):
    """Staffing dashboard view"""
    context = {}

    if is_app_installed('staffing'):
        from staffing.models import StaffProfile, Department, Shift, TimeOffRequest

        # Get staffing statistics
        context['total_staff'] = StaffProfile.objects.filter(is_active=True).count()
        context['departments'] = Department.objects.filter(is_active=True)

        # Get upcoming shifts
        today = timezone.now()
        context['upcoming_shifts'] = Shift.objects.filter(
            start_time__gte=today
        ).order_by('start_time')[:10]

        # Get pending time off requests
        context['pending_requests'] = TimeOffRequest.objects.filter(status='pending').order_by('start_date')[:5]

    return render(request, 'admin_panel/staffing/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def kitchen_dashboard(request):
    """Kitchen dashboard view"""
    context = {}

    if is_app_installed('kitchen'):
        from kitchen.models import KitchenStation, OrderItemStatus, KitchenAlert

        # Get kitchen statistics
        context['stations'] = KitchenStation.objects.filter(is_active=True)

        # Get active orders
        context['active_orders'] = OrderItemStatus.objects.filter(
            status__in=['pending', 'in_progress']
        ).select_related('order_item', 'order_item__order').order_by('created_at')

        # Get active alerts
        context['active_alerts'] = KitchenAlert.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-priority', '-created_at')

    return render(request, 'admin_panel/kitchen/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def inventory_dashboard(request):
    """Inventory dashboard view"""
    context = {}

    if is_app_installed('inventory'):
        from inventory.models import InventoryItem, PurchaseOrder, InventoryCheck
        from django.db.models import F

        # Get inventory statistics
        context['total_items'] = InventoryItem.objects.filter(is_active=True).count()

        # Get low stock items
        low_stock_items = InventoryItem.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock')
        )
        context['low_stock_items'] = low_stock_items.count()
        context['low_stock_items_list'] = low_stock_items[:10]

        # Get recent purchase orders
        context['recent_orders'] = PurchaseOrder.objects.order_by('-created_at')[:5]

        # Get recent inventory checks
        context['recent_checks'] = InventoryCheck.objects.order_by('-created_at')[:5]

    return render(request, 'admin_panel/inventory/dashboard.html', context)

# Reports & Analytics views
@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    """Analytics dashboard view"""
    # Get date range for analytics
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get sales data
    total_sales = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='completed',
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0

    # Get order data
    total_orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='completed'
    ).count()

    # Get customer data
    total_customers = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        user__isnull=False
    ).values('user').distinct().count()

    # Get average order value
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0

    # Get top selling menu items
    top_items = OrderItem.objects.filter(
        order__created_at__date__range=[start_date, end_date],
        order__status='completed'
    ).values('menu_item__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'avg_order_value': avg_order_value,
        'top_items': top_items,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'admin_panel/analytics/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def analytics_reports(request):
    """Reports view"""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get report type
    report_type = request.GET.get('type', 'sales')

    # Prepare context
    context = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
    }

    # Add report data based on type
    if report_type == 'sales':
        # Daily sales data
        sales_data = Order.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='completed',
            payment_status='paid'
        ).values('created_at__date').annotate(
            date=F('created_at__date'),
            total_sales=Sum('total'),
            order_count=Count('id')
        ).order_by('date')

        context['report_data'] = sales_data

    elif report_type == 'menu':
        # Menu item performance
        menu_data = OrderItem.objects.filter(
            order__created_at__date__range=[start_date, end_date],
            order__status='completed'
        ).values('menu_item__name').annotate(
            item_name=F('menu_item__name'),
            quantity_sold=Sum('quantity'),
            revenue=Sum(F('price') * F('quantity'))
        ).order_by('-quantity_sold')

        context['report_data'] = menu_data

    return render(request, 'admin_panel/analytics/reports.html', context)

@login_required
@user_passes_test(is_admin)
def analytics_sales(request):
    """Sales analytics view"""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get sales by date
    daily_sales = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='completed',
        payment_status='paid'
    ).values('created_at__date').annotate(
        date=F('created_at__date'),
        total_sales=Sum('total'),
        order_count=Count('id'),
        avg_order_value=Sum('total') / Count('id')
    ).order_by('date')

    # Get sales by payment method
    payment_method_sales = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='completed',
        payment_status='paid'
    ).values('payment_method').annotate(
        total_sales=Sum('total'),
        order_count=Count('id')
    ).order_by('-total_sales')

    context = {
        'daily_sales': daily_sales,
        'payment_method_sales': payment_method_sales,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'admin_panel/analytics/sales.html', context)