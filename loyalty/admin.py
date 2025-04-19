from django.contrib import admin
from .models import (
    LoyaltyTier, LoyaltyProgram, LoyaltyAccount,
    LoyaltyTransaction, LoyaltyReward, RewardRedemption
)

@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_threshold', 'discount_percentage', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_per_dollar', 'points_expiration_months', 'is_active')

@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'points_balance', 'lifetime_points', 'tier', 'enrollment_date', 'is_active')
    list_filter = ('is_active', 'tier')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('enrollment_date', 'last_activity_date')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'tier')

@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'points', 'transaction_type', 'reason', 'timestamp', 'expiration_date')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('account__user__username', 'reason', 'reference_id')
    readonly_fields = ('timestamp',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account__user')

@admin.register(LoyaltyReward)
class LoyaltyRewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_required', 'is_active', 'limited_quantity', 'quantity_available')
    list_filter = ('is_active', 'limited_quantity')
    search_fields = ('name', 'description')

@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ('reward', 'account', 'points_used', 'redemption_date', 'is_used')
    list_filter = ('is_used', 'redemption_date')
    search_fields = ('account__user__username', 'reward__name', 'redemption_code')
    readonly_fields = ('redemption_date', 'used_date')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account__user', 'reward')
