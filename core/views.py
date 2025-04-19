from django.shortcuts import render, redirect
from django.contrib import messages
from .models import TeamMember, Testimonial, Service
from menu.models import Category, MenuItem
from .forms import ContactForm

def home(request):
    # Get active menu categories
    categories = Category.objects.filter(is_active=True).order_by('display_order')

    # Get popular menu items
    popular_items = MenuItem.objects.filter(is_popular=True, is_active=True)[:8]

    # Get services
    services = Service.objects.filter(is_active=True).order_by('display_order')[:6]

    # Get testimonials
    testimonials = Testimonial.objects.filter(is_active=True)[:6]

    context = {
        'categories': categories,
        'popular_items': popular_items,
        'services': services,
        'testimonials': testimonials,
    }
    return render(request, 'core/index.html', context)

def about(request):
    return render(request, 'core/about.html')

def service(request):
    services = Service.objects.filter(is_active=True).order_by('display_order')
    return render(request, 'core/service.html', {'services': services})

def team(request):
    team_members = TeamMember.objects.filter(is_active=True).order_by('display_order')
    return render(request, 'core/team.html', {'team_members': team_members})

def testimonial(request):
    testimonials = Testimonial.objects.filter(is_active=True)
    return render(request, 'core/testimonial.html', {'testimonials': testimonials})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('core:contact')
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})
