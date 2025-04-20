from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    # Admin views
    path('admin/', views.loyalty_dashboard, name='dashboard'),
    path('admin/accounts/', views.loyalty_accounts, name='accounts'),
    path('admin/account/<int:account_id>/', views.loyalty_account_detail, name='account_detail'),
    path('admin/tiers/', views.loyalty_tiers, name='tiers'),
    path('admin/rewards/', views.loyalty_rewards, name='rewards'),
    path('admin/reward/<int:reward_id>/', views.loyalty_reward_detail, name='reward_detail'),
    path('admin/transactions/', views.loyalty_transactions, name='transactions'),
    path('admin/redemptions/', views.reward_redemptions, name='redemptions'),
    path('admin/settings/', views.loyalty_settings, name='settings'),

    # User-facing views
    path('', views.user_dashboard, name='user_dashboard'),
    path('rewards/', views.user_rewards, name='user_rewards'),
    path('transactions/', views.user_transactions, name='user_transactions'),
    path('redemptions/', views.user_redemptions, name='user_redemptions'),
    path('redeem/<int:reward_id>/', views.redeem_reward, name='redeem_reward'),
]
