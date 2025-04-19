from django import forms
from .models import Booking
from django.utils import timezone

class DateTimePickerInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'email', 'phone', 'date_time', 'num_people', 'special_request']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Phone'}),
            'date_time': DateTimePickerInput(attrs={'class': 'form-control'}),
            'num_people': forms.Select(attrs={'class': 'form-select'}, choices=[(i, f'People {i}') for i in range(1, 21)]),
            'special_request': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Special Request', 'style': 'height: 100px'}),
        }
    
    def clean_date_time(self):
        date_time = self.cleaned_data.get('date_time')
        if date_time < timezone.now():
            raise forms.ValidationError("Booking time cannot be in the past!")
        return date_time
