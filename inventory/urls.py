from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='dashboard'),
    path('items/', views.inventory_items, name='items'),
    path('item/<int:item_id>/', views.inventory_item_detail, name='item_detail'),
    path('suppliers/', views.suppliers, name='suppliers'),
    path('supplier/<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('purchase-orders/', views.purchase_orders, name='purchase_orders'),
    path('purchase-order/<int:order_id>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('inventory-checks/', views.inventory_checks, name='inventory_checks'),
    path('inventory-check/<int:check_id>/', views.inventory_check_detail, name='inventory_check_detail'),
]
