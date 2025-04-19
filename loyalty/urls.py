from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    path('', views.loyalty_dashboard, name='dashboard'),
    path('accounts/', views.loyalty_accounts, name='accounts'),
    path('account/<int:account_id>/', views.loyalty_account_detail, name='account_detail'),
    path('tiers/', views.loyalty_tiers, name='tiers'),
    path('rewards/', views.loyalty_rewards, name='rewards'),
    path('reward/<int:reward_id>/', views.loyalty_reward_detail, name='reward_detail'),
    path('transactions/', views.loyalty_transactions, name='transactions'),
    path('redemptions/', views.reward_redemptions, name='redemptions'),
    path('settings/', views.loyalty_settings, name='settings'),
]
