"""
URL configuration for restaurant_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Renamed Django admin URL
    path('', include('core.urls')),
    path('menu/', include('menu.urls')),
    path('booking/', include('booking.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('reviews/', include('reviews.urls')),
    path('admin/', include('admin_panel.urls')),  # Our custom admin panel
    path('kitchen/', include('kitchen.urls')),  # Kitchen display system
    path('inventory/', include('inventory.urls')),  # Inventory management system
    path('staffing/', include('staffing.urls')),  # Staff management system
    path('analytics/', include('analytics.urls')),  # Analytics dashboard
    path('loyalty/', include('loyalty.urls')),  # Loyalty program management
    path('ai/', include('ai_features.urls')),  # AI features
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
