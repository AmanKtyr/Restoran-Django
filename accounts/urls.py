from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('register/<str:referral_code>/', views.register_with_referral, name='register_with_referral'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),

    # Profile and Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/activity-history/', views.activity_history, name='activity_history'),

    # Address Management
    path('profile/addresses/', views.address_list, name='address_list'),
    path('profile/addresses/add/', views.add_address, name='add_address'),
    path('profile/addresses/<int:address_id>/edit/', views.edit_address, name='edit_address'),
    path('profile/addresses/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('profile/addresses/<int:address_id>/set-default/', views.set_default_address, name='set_default_address'),

    # Favorites
    path('profile/favorites/', views.favorites_list, name='favorites_list'),
    path('profile/favorites/add/<str:content_type>/<int:object_id>/', views.add_favorite, name='add_favorite'),
    path('profile/favorites/remove/<int:favorite_id>/', views.remove_favorite, name='remove_favorite'),

    # Referrals
    path('profile/referrals/', views.referrals_view, name='referrals'),
    path('profile/referrals/share/', views.share_referral, name='share_referral'),
]
