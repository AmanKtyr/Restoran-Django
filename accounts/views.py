from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import JsonResponse, Http404
from django.conf import settings
from django.urls import reverse
from datetime import timedelta

from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, UserForm, UserAddressForm
from .models import UserProfile, UserActivity, UserAddress, UserFavorite, EmailVerificationToken, ReferralBonus
from .utils import send_verification_email, send_welcome_email, process_referral, complete_referral

def register_view(request):
    """Register a new user"""
    # Check if user is already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('core:home')

    referral_code = request.session.get('referral_code', None)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create the user but don't log them in yet
            user = form.save()

            # Process referral if available
            if referral_code:
                process_referral(referral_code, user)
                # Clear the referral code from session
                del request.session['referral_code']

            # Send verification email
            send_verification_email(user, request)

            # Send welcome email
            send_welcome_email(user)

            # Log the registration activity
            UserActivity.log_activity(
                user=user,
                activity_type='register',
                description='User registered a new account',
                request=request
            )

            messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'referral_code': referral_code
    })


def register_with_referral(request, referral_code):
    """Register with a referral code"""
    # Store the referral code in session
    request.session['referral_code'] = referral_code

    # Redirect to the regular registration page
    return redirect('accounts:register')

def login_view(request):
    """Log in a user"""
    # Check if user is already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('core:home')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if user has a profile, create one if not
                try:
                    user.profile
                except User.profile.RelatedObjectDoesNotExist:
                    UserProfile.objects.create(user=user)

                # Check if email is verified
                if not user.profile.email_verified:
                    messages.warning(request, 'Please verify your email address before logging in. Check your inbox for the verification link.')
                    return redirect('accounts:resend_verification')

                login(request, user)

                # Update last login time in profile
                user.profile.last_login_at = timezone.now()
                user.profile.save(update_fields=['last_login_at'])

                # Log the login activity
                UserActivity.log_activity(
                    user=user,
                    activity_type='login',
                    description='User logged in',
                    request=request
                )

                messages.success(request, f'Welcome back, {user.first_name}!')
                # Redirect to the page user was trying to access or home
                next_page = request.GET.get('next', 'core:home')
                return redirect(next_page)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    # Log the logout activity before logging out
    if request.user.is_authenticated:
        UserActivity.log_activity(
            user=request.user,
            activity_type='logout',
            description='User logged out',
            request=request
        )

    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')

@login_required
def profile_view(request):
    # Check if user has a profile, create one if not
    try:
        request.user.profile
    except User.profile.RelatedObjectDoesNotExist:
        UserProfile.objects.create(user=request.user)

    return render(request, 'accounts/profile.html')

@login_required
@transaction.atomic
def edit_profile(request):
    # Check if user has a profile, create one if not
    try:
        profile = request.user.profile
    except User.profile.RelatedObjectDoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            # Log the profile update activity
            UserActivity.log_activity(
                user=request.user,
                activity_type='profile_update',
                description='User updated their profile',
                request=request
            )

            messages.success(request, 'Your profile was successfully updated!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def dashboard_view(request):
    """User dashboard view showing profile, orders, bookings, and reviews"""
    # Check if user has a profile, create one if not
    try:
        profile = request.user.profile
    except User.profile.RelatedObjectDoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    # Get user activities for dashboard
    activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:10]

    # Get user addresses
    addresses = UserAddress.objects.filter(user=request.user)

    # Get user favorites
    user_favorites = UserFavorite.objects.filter(user=request.user).order_by('-created_at')

    # Get referrals made by the user
    referrals = User.objects.filter(profile__referred_by=request.user).select_related('profile')

    # Get referral bonuses
    referral_bonuses = ReferralBonus.objects.filter(
        Q(referrer=request.user) | Q(referred=request.user)
    ).select_related('referrer', 'referred')

    # Generate referral URL
    referral_url = request.build_absolute_uri(
        reverse('accounts:register_with_referral', kwargs={'referral_code': profile.referral_code})
    )

    # Initialize context with user and profile
    context = {
        'user': request.user,
        'profile': profile,
        'activities': activities,
        'addresses': addresses,
        'referrals': referrals,
        'referral_bonuses': referral_bonuses,
        'referral_url': referral_url,
        'referral_points_reward': getattr(settings, 'REFERRAL_POINTS_REWARD', 100),
    }

    # Get order statistics if orders app is installed
    try:
        from orders.models import Order

        # Get recent orders
        recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        order_count = Order.objects.filter(user=request.user).count()

        # Add to context
        context['recent_orders'] = recent_orders
        context['order_count'] = order_count
    except (ImportError, Exception):
        context['order_count'] = 0

    # Get booking statistics if booking app is installed
    try:
        from booking.models import Booking

        # Get recent bookings
        recent_bookings = Booking.objects.filter(user=request.user).order_by('-date_time')[:5]
        booking_count = Booking.objects.filter(user=request.user).count()

        # Add to context
        context['recent_bookings'] = recent_bookings
        context['booking_count'] = booking_count
    except (ImportError, Exception):
        context['booking_count'] = 0

    # Get review statistics if reviews app is installed
    try:
        from reviews.models import Review

        # Get user reviews
        user_reviews = Review.objects.filter(user=request.user).order_by('-created_at')[:5]
        review_count = Review.objects.filter(user=request.user).count()

        # Add to context
        context['user_reviews'] = user_reviews
        context['review_count'] = review_count
    except (ImportError, Exception):
        context['review_count'] = 0

    # Get loyalty account if loyalty app is installed
    try:
        from loyalty.models import LoyaltyAccount, LoyaltyTier

        # Get or create loyalty account
        loyalty_account, created = LoyaltyAccount.objects.get_or_create(
            user=request.user,
            defaults={'is_active': True}
        )

        # If account was just created, update tier
        if created:
            loyalty_account.update_tier()

        # Get all tiers for progress display
        tiers = LoyaltyTier.objects.filter(is_active=True).order_by('points_threshold')

        # Calculate next tier and progress
        next_tier = None
        tier_progress_percentage = 100
        points_needed_for_next_tier = 0

        if loyalty_account.tier:
            current_tier_threshold = loyalty_account.tier.points_threshold
            # Find next tier
            higher_tiers = tiers.filter(points_threshold__gt=current_tier_threshold)
            if higher_tiers.exists():
                next_tier = higher_tiers.first()
                points_needed_for_next_tier = next_tier.points_threshold - loyalty_account.points_balance
                # Calculate progress percentage
                if next_tier.points_threshold > current_tier_threshold:
                    points_range = next_tier.points_threshold - current_tier_threshold
                    points_earned = loyalty_account.points_balance - current_tier_threshold
                    tier_progress_percentage = min(100, int((points_earned / points_range) * 100))

        # Add to context
        context['loyalty_account'] = loyalty_account
        context['tiers'] = tiers
        context['next_tier'] = next_tier
        context['tier_progress_percentage'] = tier_progress_percentage
        context['points_needed_for_next_tier'] = points_needed_for_next_tier
    except (ImportError, Exception):
        pass

    # Get AI recommendations if ai_features app is installed
    try:
        from ai_features.models import AIRecommendation

        # Get personalized recommendations
        recommendations = AIRecommendation.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at')[:4]

        # Add to context
        context['recommendations'] = recommendations
    except (ImportError, Exception):
        pass

    # Get favorite menu items if menu app is installed
    try:
        from menu.models import MenuItem, FavoriteItem

        # Get favorite items
        favorites = FavoriteItem.objects.filter(user=request.user).select_related('menu_item')[:4]

        # Add to context
        context['favorites'] = favorites
    except (ImportError, Exception):
        pass

    return render(request, 'accounts/dashboard.html', context)

@login_required
def change_password(request):
    """View for changing user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update the session to prevent the user from being logged out
            update_session_auth_hash(request, user)

            # Log the password change activity
            UserActivity.log_activity(
                user=request.user,
                activity_type='password_change',
                description='User changed their password',
                request=request
            )

            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {
        'form': form
    })

@login_required
def activity_history(request):
    """View for displaying user activity history"""
    # Get user activities
    activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')

    # Pagination
    page = request.GET.get('page', 1)
    from django.core.paginator import Paginator
    paginator = Paginator(activities, 20)  # Show 20 activities per page
    activities_page = paginator.get_page(page)

    return render(request, 'accounts/activity_history.html', {
        'activities': activities_page
    })


# Address Management Views
@login_required
def address_list(request):
    """View for displaying user addresses"""
    addresses = UserAddress.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {
        'addresses': addresses
    })

@login_required
def add_address(request):
    """View for adding a new address"""
    if request.method == 'POST':
        form = UserAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()

            # Log the address added activity
            UserActivity.log_activity(
                user=request.user,
                activity_type='address_added',
                description=f'Added a new {address.get_address_type_display()} address',
                request=request
            )

            messages.success(request, 'Address added successfully!')
            return redirect('accounts:address_list')
    else:
        form = UserAddressForm()

    return render(request, 'accounts/address_form.html', {
        'form': form,
        'title': 'Add New Address'
    })

@login_required
def edit_address(request, address_id):
    """View for editing an existing address"""
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)

    if request.method == 'POST':
        form = UserAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()

            # Log the address updated activity
            UserActivity.log_activity(
                user=request.user,
                activity_type='address_updated',
                description=f'Updated {address.get_address_type_display()} address',
                request=request
            )

            messages.success(request, 'Address updated successfully!')
            return redirect('accounts:address_list')
    else:
        form = UserAddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {
        'form': form,
        'title': 'Edit Address',
        'address': address
    })

@login_required
def delete_address(request, address_id):
    """View for deleting an address"""
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)

    if request.method == 'POST':
        address_type = address.get_address_type_display()
        address.delete()

        # Log the address removed activity
        UserActivity.log_activity(
            user=request.user,
            activity_type='address_removed',
            description=f'Removed {address_type} address',
            request=request
        )

        messages.success(request, 'Address deleted successfully!')
        return redirect('accounts:address_list')

    return render(request, 'accounts/confirm_delete.html', {
        'object': address,
        'object_name': f'{address.name} ({address.get_address_type_display()})',
        'cancel_url': 'accounts:address_list'
    })

@login_required
def set_default_address(request, address_id):
    """View for setting an address as default"""
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)

    # Set as default (this will automatically unset any other default)
    address.is_default = True
    address.save()

    messages.success(request, f'{address.name} set as your default address.')

    # Redirect back to the address list
    return redirect('accounts:address_list')


# Favorites Management Views
@login_required
def favorites_list(request):
    """View for displaying user favorites"""
    favorites = UserFavorite.objects.filter(user=request.user).order_by('-created_at')

    # Get actual objects for each favorite
    favorites_with_objects = []
    for favorite in favorites:
        obj = None
        if favorite.content_type == 'menu_item':
            try:
                from menu.models import MenuItem
                obj = MenuItem.objects.filter(id=favorite.object_id).first()
            except (ImportError, Exception):
                pass
        elif favorite.content_type == 'category':
            try:
                from menu.models import Category
                obj = Category.objects.filter(id=favorite.object_id).first()
            except (ImportError, Exception):
                pass

        if obj:
            favorites_with_objects.append({
                'favorite': favorite,
                'object': obj
            })

    return render(request, 'accounts/favorites_list.html', {
        'favorites': favorites_with_objects
    })

@login_required
def add_favorite(request, content_type, object_id):
    """View for adding an item to favorites"""
    # Check if the object exists
    obj = None
    if content_type == 'menu_item':
        try:
            from menu.models import MenuItem
            obj = MenuItem.objects.filter(id=object_id).first()
        except (ImportError, Exception):
            pass
    elif content_type == 'category':
        try:
            from menu.models import Category
            obj = Category.objects.filter(id=object_id).first()
        except (ImportError, Exception):
            pass

    if not obj:
        raise Http404("Object not found")

    # Create favorite if it doesn't exist
    favorite, created = UserFavorite.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=object_id
    )

    if created:
        # Log the favorite activity
        UserActivity.log_activity(
            user=request.user,
            activity_type='favorite',
            description=f'Added {obj} to favorites',
            request=request,
            metadata={'content_type': content_type, 'object_id': object_id}
        )

        messages.success(request, f'{obj} added to your favorites!')
    else:
        messages.info(request, f'{obj} is already in your favorites.')

    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'created': created})

    # Otherwise redirect back to the referring page or favorites list
    next_url = request.META.get('HTTP_REFERER', 'accounts:favorites_list')
    return redirect(next_url)

@login_required
def remove_favorite(request, favorite_id):
    """View for removing an item from favorites"""
    favorite = get_object_or_404(UserFavorite, id=favorite_id, user=request.user)

    # Get object info before deleting
    content_type = favorite.content_type
    object_id = favorite.object_id

    # Delete the favorite
    favorite.delete()

    # Log the activity
    UserActivity.log_activity(
        user=request.user,
        activity_type='favorite',
        description=f'Removed item from favorites',
        request=request,
        metadata={'content_type': content_type, 'object_id': object_id, 'action': 'remove'}
    )

    messages.success(request, 'Item removed from your favorites.')

    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    # Otherwise redirect back to the favorites list
    return redirect('accounts:favorites_list')


# Email Verification Views
def verify_email(request, token):
    """Verify a user's email address using a token"""
    # Find the token
    token_obj = get_object_or_404(EmailVerificationToken, token=token)

    # Check if token is valid
    if not token_obj.is_valid():
        if token_obj.is_used:
            messages.error(request, 'This verification link has already been used.')
        else:
            messages.error(request, 'This verification link has expired. Please request a new one.')
        return redirect('accounts:resend_verification')

    # Mark the token as used
    token_obj.is_used = True
    token_obj.save(update_fields=['is_used'])

    # Mark the user's email as verified
    user = token_obj.user
    user.profile.email_verified = True
    user.profile.save(update_fields=['email_verified'])

    # Log the activity
    UserActivity.log_activity(
        user=user,
        activity_type='email_verified',
        description='Email address verified',
        request=request
    )

    # Complete referral if user was referred
    complete_referral(user)

    # Show success message
    messages.success(request, 'Your email has been verified successfully! You can now log in.')

    # Redirect to login page
    return redirect('accounts:login')


@login_required
def resend_verification(request):
    """Resend email verification link"""
    # Check if email is already verified
    if request.user.profile.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('accounts:dashboard')

    # Send verification email
    if send_verification_email(request.user, request):
        messages.success(request, 'Verification email sent. Please check your inbox.')
    else:
        messages.error(request, 'Failed to send verification email. Please try again later.')

    return render(request, 'accounts/resend_verification.html')


# Referral Views
@login_required
def referrals_view(request):
    """View for displaying user referrals and referral code"""
    # Get referrals made by the user
    referrals = User.objects.filter(profile__referred_by=request.user).select_related('profile')

    # Get referral bonuses
    bonuses = ReferralBonus.objects.filter(
        Q(referrer=request.user) | Q(referred=request.user)
    ).select_related('referrer', 'referred')

    # Generate referral URL
    referral_url = request.build_absolute_uri(
        reverse('accounts:register_with_referral', kwargs={'referral_code': request.user.profile.referral_code})
    )

    return render(request, 'accounts/referrals.html', {
        'referrals': referrals,
        'bonuses': bonuses,
        'referral_url': referral_url,
        'referral_code': request.user.profile.referral_code,
        'points_reward': settings.REFERRAL_POINTS_REWARD
    })


@login_required
def share_referral(request):
    """View for sharing referral code"""
    # Generate referral URL
    referral_url = request.build_absolute_uri(
        reverse('accounts:register_with_referral', kwargs={'referral_code': request.user.profile.referral_code})
    )

    return render(request, 'accounts/share_referral.html', {
        'referral_url': referral_url,
        'referral_code': request.user.profile.referral_code,
        'points_reward': settings.REFERRAL_POINTS_REWARD
    })
