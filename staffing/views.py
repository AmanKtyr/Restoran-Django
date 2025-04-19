from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import (
    Department, Position, StaffProfile, Skill, StaffSkill,
    Availability, TimeOffRequest, Shift, ShiftSwapRequest,
    ShiftTemplate, Schedule, ClockInOut, PayrollPeriod, PayrollRecord,
    SchedulingPreference, PerformanceReview
)

# Helper function to check if user is staff or admin
def is_staff_or_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_admin)
def staffing_dashboard(request):
    """Main staffing dashboard view"""
    # Get staffing statistics
    total_staff = StaffProfile.objects.filter(is_active=True).count()
    departments = Department.objects.filter(is_active=True)

    # Get upcoming shifts
    today = timezone.now().date()
    upcoming_shifts = Shift.objects.filter(
        date__gte=today
    ).order_by('date', 'start_time')[:10]

    # Get pending time off requests
    pending_requests = TimeOffRequest.objects.filter(status='pending').order_by('start_date')[:5]

    context = {
        'total_staff': total_staff,
        'departments': departments,
        'upcoming_shifts': upcoming_shifts,
        'pending_requests': pending_requests,
    }
    return render(request, 'staffing/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def staff_list(request):
    """View all staff members"""
    staff = StaffProfile.objects.all().select_related('user', 'position', 'position__department')

    # Filter by department if provided
    department_id = request.GET.get('department')
    if department_id:
        staff = staff.filter(position__department_id=department_id)

    # Filter by position if provided
    position_id = request.GET.get('position')
    if position_id:
        staff = staff.filter(position_id=position_id)

    # Filter by status if provided
    status = request.GET.get('status')
    if status == 'active':
        staff = staff.filter(is_active=True)
    elif status == 'inactive':
        staff = staff.filter(is_active=False)

    departments = Department.objects.filter(is_active=True)
    positions = Position.objects.filter(is_active=True)

    context = {
        'staff': staff,
        'departments': departments,
        'positions': positions,
        'selected_department': department_id,
        'selected_position': position_id,
        'selected_status': status,
    }
    return render(request, 'staffing/staff_list.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def staff_detail(request, staff_id):
    """View details of a specific staff member"""
    staff = get_object_or_404(StaffProfile, id=staff_id)
    skills = StaffSkill.objects.filter(staff=staff).select_related('skill')

    # Get upcoming shifts for this staff member
    today = timezone.now().date()
    upcoming_shifts = Shift.objects.filter(
        staff=staff,
        date__gte=today
    ).order_by('date', 'start_time')[:10]

    # Get recent time off requests
    time_off_requests = TimeOffRequest.objects.filter(staff=staff).order_by('-created_at')[:5]

    # Get recent performance reviews
    performance_reviews = PerformanceReview.objects.filter(staff=staff).order_by('-review_date')[:3]

    context = {
        'staff': staff,
        'skills': skills,
        'upcoming_shifts': upcoming_shifts,
        'time_off_requests': time_off_requests,
        'performance_reviews': performance_reviews,
    }
    return render(request, 'staffing/staff_detail.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def departments(request):
    """View all departments"""
    departments_list = Department.objects.all()

    context = {
        'departments': departments_list,
    }
    return render(request, 'staffing/departments.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def positions(request):
    """View all positions"""
    positions_list = Position.objects.all().select_related('department')

    # Filter by department if provided
    department_id = request.GET.get('department')
    if department_id:
        positions_list = positions_list.filter(department_id=department_id)

    departments = Department.objects.filter(is_active=True)

    context = {
        'positions': positions_list,
        'departments': departments,
        'selected_department': department_id,
    }
    return render(request, 'staffing/positions.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def schedule(request):
    """View staff schedule"""
    # Get the current week's schedule
    today = timezone.now().date()
    start_of_week = today - timezone.timedelta(days=today.weekday())
    end_of_week = start_of_week + timezone.timedelta(days=6)

    shifts = Shift.objects.filter(
        date__range=[start_of_week, end_of_week]
    ).select_related('staff__user', 'position')

    context = {
        'shifts': shifts,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
    }
    return render(request, 'staffing/schedule.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def shifts(request):
    """View all shifts"""
    shifts_list = Shift.objects.all().select_related('staff__user', 'position')

    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        shifts_list = shifts_list.filter(date__range=[start_date, end_date])

    # Filter by staff if provided
    staff_id = request.GET.get('staff')
    if staff_id:
        shifts_list = shifts_list.filter(staff_id=staff_id)

    # Filter by position if provided
    position_id = request.GET.get('position')
    if position_id:
        shifts_list = shifts_list.filter(position_id=position_id)

    staff = StaffProfile.objects.filter(is_active=True).select_related('user')
    positions = Position.objects.filter(is_active=True)

    context = {
        'shifts': shifts_list,
        'staff': staff,
        'positions': positions,
        'selected_staff': staff_id,
        'selected_position': position_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'staffing/shifts.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def time_off_requests(request):
    """View all time off requests"""
    requests_list = TimeOffRequest.objects.all().select_related('staff__user')

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        requests_list = requests_list.filter(status=status)

    # Filter by staff if provided
    staff_id = request.GET.get('staff')
    if staff_id:
        requests_list = requests_list.filter(staff_id=staff_id)

    staff = StaffProfile.objects.filter(is_active=True).select_related('user')

    context = {
        'requests': requests_list,
        'staff': staff,
        'selected_status': status,
        'selected_staff': staff_id,
    }
    return render(request, 'staffing/time_off_requests.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def time_off_request_detail(request, request_id):
    """View details of a specific time off request"""
    time_off_request = get_object_or_404(TimeOffRequest, id=request_id)

    context = {
        'request': time_off_request,
    }
    return render(request, 'staffing/time_off_request_detail.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def performance_reviews(request):
    """View all performance reviews"""
    reviews_list = PerformanceReview.objects.all().select_related('staff__user', 'reviewer')

    # Filter by staff if provided
    staff_id = request.GET.get('staff')
    if staff_id:
        reviews_list = reviews_list.filter(staff_id=staff_id)

    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        reviews_list = reviews_list.filter(status=status)

    staff = StaffProfile.objects.filter(is_active=True).select_related('user')

    context = {
        'reviews': reviews_list,
        'staff': staff,
        'selected_staff': staff_id,
        'selected_status': status,
    }
    return render(request, 'staffing/performance_reviews.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def performance_review_detail(request, review_id):
    """View details of a specific performance review"""
    review = get_object_or_404(PerformanceReview, id=review_id)

    context = {
        'review': review,
    }
    return render(request, 'staffing/performance_review_detail.html', context)
