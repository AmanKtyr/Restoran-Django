from django import forms
from .models import CustomerExperience

class CustomerExperienceForm(forms.ModelForm):
    """Form for submitting customer experiences"""
    
    class Meta:
        model = CustomerExperience
        fields = ['rating', 'comment', 'shared_on_social']
        widgets = {
            'rating': forms.RadioSelect(),
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'shared_on_social': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'rating': 'How would you rate your experience?',
            'comment': 'Tell us about your experience',
            'shared_on_social': 'I want to share my experience on social media',
        }
        help_texts = {
            'comment': 'Your feedback helps us improve our service.',
        }
