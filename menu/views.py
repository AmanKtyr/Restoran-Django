from django.shortcuts import render, get_object_or_404
from django.db.models import Q
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

    context = {
        'categories': categories,
        'menu_items': menu_items,
        'category_counts': category_counts,
        'filter_count': menu_items.count(),
        'total_count': MenuItem.objects.filter(is_active=True).count(),
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
