from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from PIL import Image
import os
from .models import Category, MenuItem

def menu_list(request):
    # Get all active categories
    categories = Category.objects.filter(is_active=True).order_by('display_order')

    # Start with all active menu items
    menu_items = MenuItem.objects.filter(is_active=True)

    # Apply filters based on request parameters
    # Dietary filters
    if request.GET.get('vegetarian'):
        menu_items = menu_items.filter(is_vegetarian=True)
    if request.GET.get('vegan'):
        menu_items = menu_items.filter(is_vegan=True)
    if request.GET.get('gluten_free'):
        menu_items = menu_items.filter(is_gluten_free=True)
    if request.GET.get('dairy_free'):
        menu_items = menu_items.filter(is_dairy_free=True)
    if request.GET.get('nut_free'):
        menu_items = menu_items.filter(is_nut_free=True)
    if request.GET.get('low_carb'):
        menu_items = menu_items.filter(is_low_carb=True)
    if request.GET.get('keto_friendly'):
        menu_items = menu_items.filter(is_keto_friendly=True)

    # Spice level filter
    if request.GET.get('spice_level'):
        menu_items = menu_items.filter(spice_level=request.GET.get('spice_level'))

    # Price range filters
    if request.GET.get('min_price'):
        menu_items = menu_items.filter(price__gte=request.GET.get('min_price'))
    if request.GET.get('max_price'):
        menu_items = menu_items.filter(price__lte=request.GET.get('max_price'))

    # Sorting
    sort_by = request.GET.get('sort_by', 'name')
    menu_items = menu_items.order_by(sort_by)

    # Count items per category for display
    category_counts = {}
    for category in categories:
        category_counts[category.id] = menu_items.filter(category=category).count()

    # Get popular items for AI recommendations
    popular_items = MenuItem.objects.filter(is_active=True, is_popular=True).order_by('?')[:8]

    context = {
        'categories': categories,
        'menu_items': menu_items,
        'category_counts': category_counts,
        'filter_count': menu_items.count(),
        'total_count': MenuItem.objects.filter(is_active=True).count(),
        'popular_items': popular_items,
    }
    return render(request, 'menu/menu.html', context)

def menu_by_category(request, category_slug):
    # Get the specific category
    category = get_object_or_404(Category, slug=category_slug, is_active=True)

    # Get all active menu items for this category
    menu_items = MenuItem.objects.filter(category=category, is_active=True).order_by('name')

    # Get all active categories for the navigation
    categories = Category.objects.filter(is_active=True).order_by('display_order')

    context = {
        'category': category,
        'categories': categories,
        'menu_items': menu_items,
    }
    return render(request, 'menu/menu_by_category.html', context)

def menu_item_detail(request, item_id):
    # Get the specific menu item
    menu_item = get_object_or_404(MenuItem, id=item_id, is_active=True)

    # Get related items (same category, excluding current item)
    related_items = MenuItem.objects.filter(
        Q(category=menu_item.category) | Q(is_popular=True),
        is_active=True
    ).exclude(id=menu_item.id).distinct()[:4]

    # Track this view for AI recommendations if user is authenticated
    if request.user.is_authenticated:
        try:
            from ai_features.models import UserInteraction
            UserInteraction.objects.create(
                user=request.user,
                menu_item=menu_item,
                interaction_type='view',
                interaction_data={'source': 'detail_page'}
            )
        except ImportError:
            # AI features app might not be installed
            pass

    # Check if user has already reviewed this item
    user_review = None
    if request.user.is_authenticated:
        from reviews.models import Review
        user_review = Review.objects.filter(user=request.user, menu_item=menu_item).first()

    context = {
        'menu_item': menu_item,
        'related_items': related_items,
        'user_review': user_review,
    }
    return render(request, 'menu/menu_item_detail.html', context)

def qr_code_generator(request):
    """Generate QR codes for the menu"""
    categories = Category.objects.filter(is_active=True).order_by('display_order')

    # Get parameters from request
    menu_type = request.GET.get('menu_type', 'full')
    category_id = request.GET.get('category_id')
    size = request.GET.get('size', 'medium')
    include_logo = request.GET.get('include_logo') == '1'

    # Initialize variables
    qr_code_url = None
    menu_url = None

    # Generate QR code if form was submitted
    if 'menu_type' in request.GET:
        # Determine the target URL
        if menu_type == 'category' and category_id:
            category = get_object_or_404(Category, id=category_id)
            menu_url = request.build_absolute_uri(reverse('menu:menu_by_category', args=[category.slug]))
        else:
            menu_url = request.build_absolute_uri(reverse('menu:menu_list'))

        # Set QR code size
        if size == 'small':
            box_size = 6
        elif size == 'large':
            box_size = 12
        else:  # medium
            box_size = 9

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=4,
        )
        qr.add_data(menu_url)
        qr.make(fit=True)

        # Create QR code image
        if include_logo:
            # Create QR with logo
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')

            # Open the logo image
            logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo.png')
            if not os.path.exists(logo_path):
                logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')

            try:
                logo = Image.open(logo_path).convert('RGBA')

                # Calculate logo size (max 30% of QR code)
                qr_width, qr_height = qr_img.size
                logo_max_size = int(min(qr_width, qr_height) * 0.3)
                logo.thumbnail((logo_max_size, logo_max_size), Image.LANCZOS)

                # Calculate position to center the logo
                logo_pos = ((qr_width - logo.size[0]) // 2, (qr_height - logo.size[1]) // 2)

                # Paste the logo onto the QR code
                qr_img.paste(logo, logo_pos, logo)

                # Convert to base64 for display
                buffer = BytesIO()
                qr_img.save(buffer, format="PNG")
                qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            except Exception as e:
                # If logo processing fails, fall back to regular QR code
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        else:
            # Regular QR code without logo
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    context = {
        'categories': categories,
        'menu_type': menu_type,
        'category_id': category_id,
        'size': size,
        'include_logo': include_logo,
        'qr_code_url': qr_code_url,
        'menu_url': menu_url,
    }

    return render(request, 'menu/qr_code_generator.html', context)
