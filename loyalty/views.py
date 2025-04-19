from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

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
