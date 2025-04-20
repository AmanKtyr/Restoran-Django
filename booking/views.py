from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from .models import Booking, BookingSettings, TimeSlot, SpecialDate, Table
from .forms import BookingForm

def booking(request):
    # Get booking settings
    settings = BookingSettings.objects.first()
    if not settings:
        settings = BookingSettings.objects.create()

    # Get available time slots
    today = timezone.now().date()
    day_of_week = today.weekday()
    time_slots = TimeSlot.objects.filter(is_active=True)

    # Check for special dates
    special_date = SpecialDate.objects.filter(date=today).first()
    is_closed = special_date.is_closed if special_date else False

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)

            # Set user if logged in
            if request.user.is_authenticated:
                booking.user = request.user

            # Set duration and end time
            booking.duration_minutes = settings.default_booking_duration_mins
            booking.end_time = booking.date_time + timezone.timedelta(minutes=booking.duration_minutes)

            # Generate confirmation code
            booking.save()
            booking.generate_confirmation_code()

            # Auto-confirm if enabled in settings
            if settings.auto_confirm_bookings:
                booking.mark_as_confirmed()

            messages.success(request, f'Your booking has been submitted successfully! Your confirmation code is {booking.confirmation_code}')
            # Store booking ID in session for the success page
            request.session['last_booking_id'] = booking.id
            return redirect('booking:booking_success')
    else:
        form = BookingForm()

    context = {
        'form': form,
        'settings': settings,
        'time_slots': time_slots,
        'is_closed': is_closed,
        'special_date': special_date,
    }

    return render(request, 'booking/booking.html', context)

def booking_success(request):
    # Get the booking from session or most recent for the user
    booking = None
    booking_id = request.session.get('last_booking_id')

    if booking_id:
        booking = Booking.objects.filter(id=booking_id).first()
        # Clear the session variable
        del request.session['last_booking_id']
    elif request.user.is_authenticated:
        booking = Booking.objects.filter(user=request.user).order_by('-created_at').first()

    return render(request, 'booking/booking_success.html', {'booking': booking})

@login_required
def my_bookings(request):
    """View for users to see their bookings"""
    bookings = Booking.objects.filter(user=request.user).order_by('-date_time')

    # Get booking settings for cancellation policy
    settings = BookingSettings.objects.first()
    if not settings:
        settings = BookingSettings.objects.create()

    context = {
        'bookings': bookings,
        'settings': settings,
    }

    return render(request, 'booking/my_bookings.html', context)

@login_required
def booking_detail(request, confirmation_code):
    """View for users to see details of a specific booking"""
    booking = get_object_or_404(Booking, confirmation_code=confirmation_code, user=request.user)

    # Get booking settings for cancellation policy
    settings = BookingSettings.objects.first()
    if not settings:
        settings = BookingSettings.objects.create()

    context = {
        'booking': booking,
        'settings': settings,
        'is_cancellable': booking.is_cancellable_online(),
    }

    return render(request, 'booking/booking_detail.html', context)

@login_required
def cancel_booking(request, confirmation_code):
    """View for users to cancel a booking"""
    booking = get_object_or_404(Booking, confirmation_code=confirmation_code, user=request.user)

    if not booking.is_cancellable_online():
        messages.error(request, 'This booking cannot be cancelled online. Please contact us directly.')
        return redirect('booking:booking_detail', confirmation_code=confirmation_code)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        booking.mark_as_cancelled(reason=reason, by='customer')
        messages.success(request, 'Your booking has been cancelled successfully.')
        return redirect('booking:my_bookings')

    return render(request, 'booking/cancel_booking.html', {'booking': booking})

def reservation_tracker(request):
    """View for tracking reservation status"""
    confirmation_code = request.GET.get('code')
    error_message = None
    booking = None

    if confirmation_code:
        # Try to find the booking
        booking = Booking.objects.filter(confirmation_code=confirmation_code).first()

        if not booking:
            error_message = "We couldn't find a reservation with that confirmation code. Please check and try again."

    context = {
        'booking': booking,
        'error_message': error_message
    }

    return render(request, 'booking/reservation_tracker.html', context)

def get_available_time_slots(request):
    """API endpoint to get available time slots for a specific date"""
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Date is required'}, status=400)

    try:
        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Check if date is in the past
    if date < timezone.now().date():
        return JsonResponse({'error': 'Date cannot be in the past'}, status=400)

    # Get booking settings
    settings = BookingSettings.objects.first()
    if not settings:
        settings = BookingSettings.objects.create()

    # Check if date is too far in the future
    max_date = timezone.now().date() + timezone.timedelta(days=settings.max_booking_days_ahead)
    if date > max_date:
        return JsonResponse({'error': f'Date cannot be more than {settings.max_booking_days_ahead} days in the future'}, status=400)

    # Check for special dates
    special_date = SpecialDate.objects.filter(date=date).first()
    if special_date and special_date.is_closed:
        return JsonResponse({'error': f'We are closed on {date} due to {special_date.name}'}, status=400)

    # Get time slots for the day of the week
    day_of_week = date.weekday()
    time_slots = TimeSlot.objects.filter(day_of_week=day_of_week, is_active=True).order_by('start_time')

    # If it's a special date with special hours, filter time slots
    if special_date and special_date.has_special_hours:
        time_slots = time_slots.filter(
            start_time__gte=special_date.opening_time,
            end_time__lte=special_date.closing_time
        )

    # Get existing bookings for the date
    start_datetime = timezone.datetime.combine(date, timezone.time.min)
    end_datetime = timezone.datetime.combine(date, timezone.time.max)
    existing_bookings = Booking.objects.filter(
        date_time__range=(start_datetime, end_datetime),
        status__in=['pending', 'confirmed', 'seated']
    )

    # Format time slots and check availability
    available_slots = []
    for slot in time_slots:
        # Count bookings in this time slot
        slot_start = timezone.datetime.combine(date, slot.start_time)
        slot_end = timezone.datetime.combine(date, slot.end_time)
        bookings_in_slot = existing_bookings.filter(
            date_time__gte=slot_start,
            date_time__lt=slot_end
        ).count()

        # Check if slot is available
        is_available = True
        if slot.max_bookings > 0 and bookings_in_slot >= slot.max_bookings:
            is_available = False

        # Check if slot is in the past for today
        if date == timezone.now().date() and slot.start_time < timezone.now().time():
            is_available = False

        available_slots.append({
            'id': slot.id,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'is_available': is_available,
            'bookings_count': bookings_in_slot,
            'max_bookings': slot.max_bookings,
        })

    return JsonResponse({
        'date': date.strftime('%Y-%m-%d'),
        'day_of_week': day_of_week,
        'day_name': date.strftime('%A'),
        'is_special_date': special_date is not None,
        'special_date_name': special_date.name if special_date else None,
        'time_slots': available_slots,
    })
