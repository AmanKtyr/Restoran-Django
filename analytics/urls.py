from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('sales/', views.sales_analytics, name='sales'),
    path('customers/', views.customer_analytics, name='customers'),
    path('menu/', views.menu_analytics, name='menu'),
    path('marketing/', views.marketing_analytics, name='marketing'),
    path('reports/', views.reports, name='reports'),
    path('export/<str:report_type>/', views.export_report, name='export_report'),
]
