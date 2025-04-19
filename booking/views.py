from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Booking
from .forms import BookingForm

def booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your booking has been submitted successfully!')
            return redirect('booking:booking_success')
    else:
        form = BookingForm()

    return render(request, 'booking/booking.html', {'form': form})

def booking_success(request):
    return render(request, 'booking/booking_success.html')
