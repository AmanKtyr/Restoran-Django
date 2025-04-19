from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.booking, name='booking'),
    path('success/', views.booking_success, name='booking_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<str:confirmation_code>/', views.booking_detail, name='booking_detail'),
    path('booking/<str:confirmation_code>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('api/available-time-slots/', views.get_available_time_slots, name='available_time_slots'),
]
