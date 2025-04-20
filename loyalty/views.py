from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from datetime import timedelta
import uuid

from .models import (
    LoyaltyTier, LoyaltyProgram, LoyaltyAccount,
    LoyaltyTransaction, LoyaltyReward, RewardRedemption
)
from django.contrib.auth.models import User

# Helper function to check if user is staff or admin
def is_staff_or_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_admin)
def loyalty_dashboard(request):
    """Main loyalty program dashboard view"""
    # Get loyalty program statistics
    total_accounts = LoyaltyAccount.objects.filter(is_active=True).count()
    total_points_issued = LoyaltyTransaction.objects.filter(transaction_type='earn').aggregate(total=Sum('points'))['total'] or 0
    total_points_redeemed = LoyaltyTransaction.objects.filter(transaction_type='redeem').aggregate(total=Sum('points'))['total'] or 0
    total_redemptions = RewardRedemption.objects.count()

    # Get loyalty program settings
    try:
        program = LoyaltyProgram.objects.get(is_active=True)
    except LoyaltyProgram.DoesNotExist:
        program = None

    # Get loyalty tiers
    tiers = LoyaltyTier.objects.filter(is_active=True).order_by('points_threshold')

    # Get recent transactions
    recent_transactions = LoyaltyTransaction.objects.all().order_by('-created_at')[:10]

    # Get recent redemptions
    recent_redemptions = RewardRedemption.objects.all().order_by('-redeemed_at')[:10]

    context = {
        'total_accounts': total_accounts,
        'total_points_issued': total_points_issued,
        'total_points_redeemed': total_points_redeemed,
        'total_redemptions': total_redemptions,
        'program': program,
        'tiers': tiers,
        'recent_transactions': recent_transactions,
        'recent_redemptions': recent_redemptions,
    }
    return render(request, 'loyalty/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def loyalty_accounts(request):
    """View all loyalty accounts"""
    accounts = LoyaltyAccount.objects.all().select_related('user', 'tier')

    # Filter by tier if provided
    tier_id = request.GET.get('tier')
    if tier_id:
        accounts = accounts.filter(tier_id=tier_id)

    # Filter by status if provided
    status = request.GET.get('status')
    if status == 'active':
        accounts = accounts.filter(is_active=True)
    elif status == 'inactive':
        accounts = accounts.filter(is_active=False)

    # Search by user if provided
    search = request.GET.get('search')
    if search:
        accounts = accounts.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )

    tiers = LoyaltyTier.objects.filter(is_active=True)

    context = {
        'accounts': accounts,
        'tiers': tiers,
        'selected_tier': tier_id,
        'selected_status': status,
        'search': search,
    }
    return render(request, 'loyalty/accounts.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def loyalty_account_detail(request, account_id):
    """View details of a specific loyalty account"""
    account = get_object_or_404(LoyaltyAccount, id=account_id)

    # Get transaction history
    transactions = LoyaltyTransaction.objects.filter(account=account).order_by('-created_at')

    # Get redemption history
    redemptions = RewardRedemption.objects.filter(account=account).order_by('-redeemed_at')

    context = {
        'account': account,
        'transactions': transactions,
        'redemptions': redemptions,
    }
    return render(request, 'loyalty/account_detail.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def loyalty_tiers(request):
    """View all loyalty tiers"""
    tiers = LoyaltyTier.objects.all().order_by('points_threshold')

    # Get accounts count per tier
    for tier in tiers:
        tier.account_count = LoyaltyAccount.objects.filter(tier=tier).count()

    context = {
        'tiers': tiers,
    }
    return render(request, 'loyalty/tiers.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def loyalty_rewards(request):
    """View all loyalty rewards"""
    rewards = LoyaltyReward.objects.all().order_by('points_required')

    # Filter by status if provided
    status = request.GET.get('status')
    if status == 'active':
        rewards = rewards.filter(is_active=True)
    elif status == 'inactive':
        rewards = rewards.filter(is_active=False)

    context = {
        'rewards': rewards,
        'selected_status': status,
    }
    return render(request, 'loyalty/rewards.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def loyalty_reward_detail(request, reward_id):
    """View details of a specific loyalty reward"""
    reward = get_object_or_404(LoyaltyReward, id=reward_id)

    # Get redemption history for this reward
    redemptions = RewardRedemption.objects.filter(reward=reward).order_by('-redeemed_at')

    context = {
        'reward': reward,
        'redemptions': redemptions,
    }
    return render(request, 'loyalty/reward_detail.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def loyalty_transactions(request):
    """View all loyalty transactions"""
    transactions = LoyaltyTransaction.objects.all().select_related('account__user').order_by('-created_at')

    # Filter by transaction type if provided
    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        try:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions = transactions.filter(created_at__date__range=[start_date, end_date])
        except ValueError:
            pass

    context = {
        'transactions': transactions,
        'selected_type': transaction_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'loyalty/transactions.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def reward_redemptions(request):
    """View all reward redemptions"""
    redemptions = RewardRedemption.objects.all().select_related('account__user', 'reward').order_by('-redeemed_at')

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        redemptions = redemptions.filter(status=status)

    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        try:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            redemptions = redemptions.filter(redeemed_at__date__range=[start_date, end_date])
        except ValueError:
            pass

    context = {
        'redemptions': redemptions,
        'selected_status': status,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'loyalty/redemptions.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def loyalty_settings(request):
    """View and edit loyalty program settings"""
    try:
        program = LoyaltyProgram.objects.get(is_active=True)
    except LoyaltyProgram.DoesNotExist:
        program = None

    context = {
        'program': program,
    }
    return render(request, 'loyalty/settings.html', context)


# User-facing loyalty views
@login_required
def user_dashboard(request):
    """User loyalty dashboard view"""
    # Get or create loyalty account for the user
    account, created = LoyaltyAccount.objects.get_or_create(
        user=request.user,
        defaults={'is_active': True}
    )

    # If account was just created, update tier
    if created:
        account.update_tier()

    # Get loyalty program settings
    try:
        program = LoyaltyProgram.objects.get(is_active=True)
    except LoyaltyProgram.DoesNotExist:
        program = None

    # Get all tiers for progress display
    tiers = LoyaltyTier.objects.filter(is_active=True).order_by('points_threshold')

    # Calculate next tier and progress
    next_tier = None
    tier_progress_percentage = 100
    points_needed_for_next_tier = 0

    if account.tier:
        # Find the next tier
        higher_tiers = tiers.filter(points_threshold__gt=account.tier.points_threshold)
        if higher_tiers.exists():
            next_tier = higher_tiers.first()
            points_needed_for_next_tier = next_tier.points_threshold - account.lifetime_points

            # Calculate progress percentage
            if account.tier.points_threshold == 0:
                current_tier_points = 0
            else:
                current_tier_points = account.tier.points_threshold

            points_range = next_tier.points_threshold - current_tier_points
            points_progress = account.lifetime_points - current_tier_points
            tier_progress_percentage = min(100, int((points_progress / points_range) * 100))

    # Get recent transactions
    recent_transactions = LoyaltyTransaction.objects.filter(account=account).order_by('-timestamp')[:5]

    # Get available rewards (that the user can afford)
    available_rewards = LoyaltyReward.objects.filter(
        is_active=True,
        points_required__lte=account.points_balance
    ).order_by('points_required')[:4]

    # Generate referral URL
    if not account.referral_code:
        account.referral_code = str(uuid.uuid4())[:8].upper()
        account.save(update_fields=['referral_code'])

    referral_url = request.build_absolute_uri(f'/register/?ref={account.referral_code}')

    context = {
        'account': account,
        'program': program,
        'tiers': tiers,
        'next_tier': next_tier,
        'tier_progress_percentage': tier_progress_percentage,
        'points_needed_for_next_tier': points_needed_for_next_tier,
        'recent_transactions': recent_transactions,
        'available_rewards': available_rewards,
        'referral_url': referral_url,
    }

    return render(request, 'loyalty/user_dashboard.html', context)

@login_required
def user_rewards(request):
    """User rewards catalog view"""
    # Get user's loyalty account
    account = get_object_or_404(LoyaltyAccount, user=request.user)

    # Get loyalty program settings
    program = get_object_or_404(LoyaltyProgram, is_active=True)

    # Get all active rewards
    rewards = LoyaltyReward.objects.filter(is_active=True)

    # Apply filters
    points_range = request.GET.get('points_range')
    selected_categories = request.GET.getlist('category')

    if points_range:
        if points_range == 'available':
            rewards = rewards.filter(points_required__lte=account.points_balance)
        elif points_range == 'under_500':
            rewards = rewards.filter(points_required__lt=500)
        elif points_range == '500_1000':
            rewards = rewards.filter(points_required__gte=500, points_required__lte=1000)
        elif points_range == '1000_2000':
            rewards = rewards.filter(points_required__gte=1000, points_required__lte=2000)
        elif points_range == 'over_2000':
            rewards = rewards.filter(points_required__gt=2000)

    # Calculate next tier and progress
    tiers = LoyaltyTier.objects.filter(is_active=True).order_by('points_threshold')
    next_tier = None
    tier_progress_percentage = 100
    points_needed_for_next_tier = 0

    if account.tier:
        # Find the next tier
        higher_tiers = tiers.filter(points_threshold__gt=account.tier.points_threshold)
        if higher_tiers.exists():
            next_tier = higher_tiers.first()
            points_needed_for_next_tier = next_tier.points_threshold - account.lifetime_points

            # Calculate progress percentage
            if account.tier.points_threshold == 0:
                current_tier_points = 0
            else:
                current_tier_points = account.tier.points_threshold

            points_range = next_tier.points_threshold - current_tier_points
            points_progress = account.lifetime_points - current_tier_points
            tier_progress_percentage = min(100, int((points_progress / points_range) * 100))

    context = {
        'account': account,
        'program': program,
        'rewards': rewards,
        'points_range': points_range,
        'selected_categories': selected_categories,
        'next_tier': next_tier,
        'tier_progress_percentage': tier_progress_percentage,
        'points_needed_for_next_tier': points_needed_for_next_tier,
    }

    return render(request, 'loyalty/user_rewards.html', context)

@login_required
def user_transactions(request):
    """User transaction history view"""
    # Get user's loyalty account
    account = get_object_or_404(LoyaltyAccount, user=request.user)

    # Get loyalty program settings
    program = get_object_or_404(LoyaltyProgram, is_active=True)

    # Get all transactions for this user
    transactions = LoyaltyTransaction.objects.filter(account=account).order_by('-timestamp')

    # Apply filters
    transaction_type = request.GET.get('type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    if start_date and end_date:
        try:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions = transactions.filter(timestamp__date__range=[start_date, end_date])
        except ValueError:
            pass

    # Calculate totals
    total_earned = transactions.filter(transaction_type='earn').aggregate(total=Sum('points'))['total'] or 0
    total_spent = transactions.filter(transaction_type='redeem').aggregate(total=Sum('points'))['total'] or 0

    # Paginate transactions
    paginator = Paginator(transactions, 10)  # 10 transactions per page
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    # Calculate next tier and progress
    tiers = LoyaltyTier.objects.filter(is_active=True).order_by('points_threshold')
    next_tier = None
    tier_progress_percentage = 100
    points_needed_for_next_tier = 0

    if account.tier:
        # Find the next tier
        higher_tiers = tiers.filter(points_threshold__gt=account.tier.points_threshold)
        if higher_tiers.exists():
            next_tier = higher_tiers.first()
            points_needed_for_next_tier = next_tier.points_threshold - account.lifetime_points

            # Calculate progress percentage
            if account.tier.points_threshold == 0:
                current_tier_points = 0
            else:
                current_tier_points = account.tier.points_threshold

            points_range = next_tier.points_threshold - current_tier_points
            points_progress = account.lifetime_points - current_tier_points
            tier_progress_percentage = min(100, int((points_progress / points_range) * 100))

    context = {
        'account': account,
        'program': program,
        'transactions': transactions,
        'transaction_type': transaction_type,
        'start_date': start_date,
        'end_date': end_date,
        'total_earned': total_earned,
        'total_spent': total_spent,
        'next_tier': next_tier,
        'tier_progress_percentage': tier_progress_percentage,
        'points_needed_for_next_tier': points_needed_for_next_tier,
    }

    return render(request, 'loyalty/user_transactions.html', context)

@login_required
def user_redemptions(request):
    """User redemption history view"""
    # Get user's loyalty account
    account = get_object_or_404(LoyaltyAccount, user=request.user)

    # Get loyalty program settings
    program = get_object_or_404(LoyaltyProgram, is_active=True)

    # Get all redemptions for this user
    redemptions = RewardRedemption.objects.filter(account=account).order_by('-redemption_date')

    # Add is_expired property to each redemption
    for redemption in redemptions:
        if redemption.expiration_date and timezone.now() > redemption.expiration_date:
            redemption.is_expired = True
        else:
            redemption.is_expired = False

    # Calculate next tier and progress
    tiers = LoyaltyTier.objects.filter(is_active=True).order_by('points_threshold')
    next_tier = None
    tier_progress_percentage = 100
    points_needed_for_next_tier = 0

    if account.tier:
        # Find the next tier
        higher_tiers = tiers.filter(points_threshold__gt=account.tier.points_threshold)
        if higher_tiers.exists():
            next_tier = higher_tiers.first()
            points_needed_for_next_tier = next_tier.points_threshold - account.lifetime_points

            # Calculate progress percentage
            if account.tier.points_threshold == 0:
                current_tier_points = 0
            else:
                current_tier_points = account.tier.points_threshold

            points_range = next_tier.points_threshold - current_tier_points
            points_progress = account.lifetime_points - current_tier_points
            tier_progress_percentage = min(100, int((points_progress / points_range) * 100))

    context = {
        'account': account,
        'program': program,
        'redemptions': redemptions,
        'next_tier': next_tier,
        'tier_progress_percentage': tier_progress_percentage,
        'points_needed_for_next_tier': points_needed_for_next_tier,
    }

    return render(request, 'loyalty/user_redemptions.html', context)

@login_required
def redeem_reward(request, reward_id):
    """Redeem a reward"""
    # Get the reward
    reward = get_object_or_404(LoyaltyReward, id=reward_id, is_active=True)

    # Get user's loyalty account
    account = get_object_or_404(LoyaltyAccount, user=request.user)

    # Check if user has enough points
    if account.points_balance < reward.points_required:
        messages.error(request, f"You don't have enough points to redeem this reward. You need {reward.points_required - account.points_balance} more points.")
        return redirect('loyalty:user_rewards')

    # Check if reward is available (quantity)
    if reward.limited_quantity and reward.quantity_available <= 0:
        messages.error(request, "This reward is no longer available.")
        return redirect('loyalty:user_rewards')

    # Process the redemption
    with transaction.atomic():
        # Deduct points from account
        account.points_balance -= reward.points_required
        account.save(update_fields=['points_balance'])

        # Create transaction record
        transaction_obj = LoyaltyTransaction.objects.create(
            account=account,
            points=reward.points_required,
            transaction_type='redeem',
            reason=f"Redeemed for {reward.name}"
        )

        # Generate unique redemption code
        redemption_code = f"{account.user.username[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

        # Calculate expiration date (30 days from now)
        expiration_date = timezone.now() + timedelta(days=30)

        # Create redemption record
        redemption = RewardRedemption.objects.create(
            account=account,
            reward=reward,
            points_used=reward.points_required,
            redemption_code=redemption_code,
            expiration_date=expiration_date
        )

        # Update reward quantity if limited
        if reward.limited_quantity:
            reward.quantity_available -= 1
            reward.save(update_fields=['quantity_available'])

    messages.success(request, f"You have successfully redeemed {reward.name} for {reward.points_required} points!")

    # Redirect to redemption confirmation page
    return render(request, 'loyalty/redeem_confirmation.html', {
        'redemption': redemption,
        'account': account,
    })
