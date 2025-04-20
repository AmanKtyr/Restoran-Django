from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, UserAddress, UserFavorite

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            # Basic info
            'phone', 'profile_picture', 'date_of_birth', 'bio',
            # Address info
            'address', 'city', 'state', 'postal_code', 'country',
            # Preferences
            'dietary_preference', 'food_allergies', 'spice_preference', 'favorite_cuisine',
            # Communication preferences
            'is_subscribed_to_newsletter', 'receive_order_updates', 'receive_promotional_emails', 'receive_sms_notifications',
            # Social media
            'facebook_profile', 'instagram_profile', 'twitter_profile',
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'food_allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'dietary_preference': forms.Select(attrs={'class': 'form-select'}),
            'spice_preference': forms.Select(attrs={'class': 'form-select'}),
            'is_subscribed_to_newsletter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_order_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_promotional_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name not in ['profile_picture', 'date_of_birth', 'is_subscribed_to_newsletter',
                                  'receive_order_updates', 'receive_promotional_emails', 'receive_sms_notifications',
                                  'dietary_preference', 'spice_preference']:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ('name', 'address_type', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'phone', 'is_default')
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name not in ['address_type', 'is_default']:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label
