from django.urls import path
from . import views

app_name = 'staffing'

urlpatterns = [
    path('', views.staffing_dashboard, name='dashboard'),
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('departments/', views.departments, name='departments'),
    path('positions/', views.positions, name='positions'),
    path('schedule/', views.schedule, name='schedule'),
    path('shifts/', views.shifts, name='shifts'),
    path('time-off/', views.time_off_requests, name='time_off_requests'),
    path('time-off/<int:request_id>/', views.time_off_request_detail, name='time_off_request_detail'),
    path('performance/', views.performance_reviews, name='performance_reviews'),
    path('performance/<int:review_id>/', views.performance_review_detail, name='performance_review_detail'),
]
