from django import forms
from .models import Booking
from django.utils import timezone

class DateTimePickerInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'email', 'phone', 'date_time', 'guest_count_adults', 'guest_count_children',
                 'occasion', 'preferred_seating_area', 'special_request', 'dietary_requirements']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Phone'}),
            'date_time': DateTimePickerInput(attrs={'class': 'form-control'}),
            'guest_count_adults': forms.Select(attrs={'class': 'form-select'}, choices=[(i, f'{i} Adults') for i in range(1, 21)]),
            'guest_count_children': forms.Select(attrs={'class': 'form-select'}, choices=[(i, f'{i} Children') for i in range(0, 11)]),
            'occasion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Special Occasion (Birthday, Anniversary, etc.)'}),
            'preferred_seating_area': forms.Select(attrs={'class': 'form-select'}),
            'special_request': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Special Requests', 'style': 'height: 100px'}),
            'dietary_requirements': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Any dietary requirements or allergies?', 'style': 'height: 100px'}),
        }

    def clean_date_time(self):
        date_time = self.cleaned_data.get('date_time')
        if date_time < timezone.now():
            raise forms.ValidationError("Booking time cannot be in the past!")
        return date_time
