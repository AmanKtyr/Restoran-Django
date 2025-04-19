from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    path('', views.kitchen_dashboard, name='dashboard'),
    path('station/<int:station_id>/', views.station_view, name='station'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('item-status/<int:item_status_id>/update/', views.update_order_item_status, name='update_item_status'),
    path('item-status/<int:item_status_id>/assign/', views.assign_order_item, name='assign_item'),
    path('alert/create/', views.create_alert, name='create_alert'),
    path('alert/<int:alert_id>/dismiss/', views.dismiss_alert, name='dismiss_alert'),
    path('api/updates/', views.get_order_updates, name='get_updates'),
]
