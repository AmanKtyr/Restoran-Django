from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg

from .models import Review, ReviewLike
from .forms import ReviewForm
from menu.models import MenuItem
from orders.models import OrderItem

@login_required
def add_review(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_active=True)

    # Check if user has ordered this item before
    has_ordered = OrderItem.objects.filter(
        order__user=request.user,
        menu_item=menu_item,
        order__status__in=['delivered', 'completed']
    ).exists()

    # Check if user has already reviewed this item
    existing_review = Review.objects.filter(user=request.user, menu_item=menu_item).first()

    if existing_review:
        messages.warning(request, "You have already reviewed this item.")
        return redirect('menu:menu_item_detail', item_id=menu_item_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.menu_item = menu_item

            # If user has ordered this item, link the review to the most recent order item
            if has_ordered:
                order_item = OrderItem.objects.filter(
                    order__user=request.user,
                    menu_item=menu_item,
                    order__status__in=['delivered', 'completed']
                ).order_by('-order__created_at').first()
                review.order_item = order_item

            review.save()
            messages.success(request, "Your review has been submitted successfully!")
            return redirect('menu:menu_item_detail', item_id=menu_item_id)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'menu_item': menu_item,
        'has_ordered': has_ordered,
    }
    return render(request, 'reviews/add_review.html', context)

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    menu_item = review.menu_item

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated successfully!")
            return redirect('menu:menu_item_detail', item_id=menu_item.id)
    else:
        form = ReviewForm(instance=review)

    context = {
        'form': form,
        'menu_item': menu_item,
        'review': review,
        'is_edit': True,
    }
    return render(request, 'reviews/add_review.html', context)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    menu_item_id = review.menu_item.id

    if request.method == 'POST':
        review.delete()
        messages.success(request, "Your review has been deleted successfully!")
        return redirect('menu:menu_item_detail', item_id=menu_item_id)

    context = {
        'review': review,
    }
    return render(request, 'reviews/delete_review.html', context)

@login_required
def like_review(request, review_id):
    if request.method == 'POST':
        review = get_object_or_404(Review, id=review_id)

        # Check if user has already liked this review
        like, created = ReviewLike.objects.get_or_create(user=request.user, review=review)

        if not created:
            # User already liked this review, so unlike it
            like.delete()
            liked = False
        else:
            liked = True

        # Get updated like count
        like_count = review.likes.count()

        # If AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'liked': liked,
                'like_count': like_count
            })

        # Otherwise redirect back to the menu item detail page
        return redirect('menu:menu_item_detail', item_id=review.menu_item.id)

    # If not POST, redirect to the menu item detail page
    return redirect('menu:menu_list')

def menu_item_reviews(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_active=True)
    reviews = Review.objects.filter(menu_item=menu_item, is_approved=True).order_by('-created_at')

    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    # Check if user has already reviewed this item
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(user=request.user, menu_item=menu_item).first()

    context = {
        'menu_item': menu_item,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'user_review': user_review,
    }
    return render(request, 'reviews/menu_item_reviews.html', context)
