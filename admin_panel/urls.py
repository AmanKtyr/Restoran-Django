from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),

    # Menu management
    path('menu/', views.menu_list, name='menu_list'),
    path('menu/categories/', views.category_list, name='category_list'),
    path('menu/categories/add/', views.category_add, name='category_add'),
    path('menu/categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('menu/categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    path('menu/items/', views.menu_item_list, name='menu_item_list'),
    path('menu/items/add/', views.menu_item_add, name='menu_item_add'),
    path('menu/items/edit/<int:pk>/', views.menu_item_edit, name='menu_item_edit'),
    path('menu/items/delete/<int:pk>/', views.menu_item_delete, name='menu_item_delete'),

    # Booking management
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/add/', views.booking_add, name='booking_add'),
    path('bookings/edit/<int:pk>/', views.booking_edit, name='booking_edit'),
    path('bookings/delete/<int:pk>/', views.booking_delete, name='booking_delete'),

    # User management
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),

    # Order management
    path('orders/', views.order_list, name='order_list'),
    path('orders/view/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/edit/<int:pk>/', views.order_edit, name='order_edit'),

    # Review management
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/view/<int:pk>/', views.review_detail, name='review_detail'),
    path('reviews/edit/<int:pk>/', views.review_edit, name='review_edit'),
    path('reviews/delete/<int:pk>/', views.review_delete, name='review_delete'),

    # Team management
    path('team/', views.team_list, name='team_list'),
    path('team/add/', views.team_add, name='team_add'),
    path('team/edit/<int:pk>/', views.team_edit, name='team_edit'),
    path('team/delete/<int:pk>/', views.team_delete, name='team_delete'),

    # Testimonial management
    path('testimonials/', views.testimonial_list, name='testimonial_list'),
    path('testimonials/add/', views.testimonial_add, name='testimonial_add'),
    path('testimonials/edit/<int:pk>/', views.testimonial_edit, name='testimonial_edit'),
    path('testimonials/delete/<int:pk>/', views.testimonial_delete, name='testimonial_delete'),

    # Service management
    path('services/', views.service_list, name='service_list'),
    path('services/add/', views.service_add, name='service_add'),
    path('services/edit/<int:pk>/', views.service_edit, name='service_edit'),
    path('services/delete/<int:pk>/', views.service_delete, name='service_delete'),

    # Contact message management
    path('messages/', views.message_list, name='message_list'),
    path('messages/view/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/delete/<int:pk>/', views.message_delete, name='message_delete'),

    # Settings
    path('settings/', views.settings, name='settings'),

    # Marketing campaigns
    path('marketing/campaigns/', views.campaign_list, name='campaign_list'),
    path('marketing/campaigns/add/', views.campaign_add, name='campaign_add'),
    path('marketing/campaigns/view/<int:pk>/', views.campaign_detail, name='campaign_detail'),
    path('marketing/campaigns/edit/<int:pk>/', views.campaign_edit, name='campaign_edit'),
    path('marketing/campaigns/delete/<int:pk>/', views.campaign_delete, name='campaign_delete'),
    path('marketing/campaigns/<int:pk>/add-performance/', views.add_campaign_performance, name='add_campaign_performance'),
]
