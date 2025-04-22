# Restoran - Django Restaurant Website

A restaurant website built with Django that includes an admin panel to manage the menu, bookings, team members, testimonials, and more.

## Features

- Responsive design
- Menu management
- Online booking system
- Contact form
- Admin panel for content management

## Project Structure

```
Restoran-Django/
├── booking/                  # Booking app
│   ├── migrations/           # Database migrations
│   ├── admin.py              # Admin panel configuration
│   ├── forms.py              # Forms for booking
│   ├── models.py             # Database models
│   ├── urls.py               # URL routing
│   └── views.py              # View functions
├── core/                     # Core app
│   ├── migrations/           # Database migrations
│   ├── admin.py              # Admin panel configuration
│   ├── forms.py              # Forms for contact
│   ├── models.py             # Database models
│   ├── urls.py               # URL routing
│   └── views.py              # View functions
├── media/                    # User-uploaded media files
├── menu/                     # Menu app
│   ├── migrations/           # Database migrations
│   ├── admin.py              # Admin panel configuration
│   ├── models.py             # Database models
│   ├── urls.py               # URL routing
│   └── views.py              # View functions
├── restaurant_project/       # Project settings
│   ├── settings.py           # Project settings
│   ├── urls.py               # Main URL routing
│   ├── wsgi.py               # WSGI configuration
│   └── asgi.py               # ASGI configuration
├── static/                   # Static files
│   ├── css/                  # CSS files
│   ├── img/                  # Image files
│   ├── js/                   # JavaScript files
│   └── lib/                  # Third-party libraries
├── templates/                # HTML templates
│   ├── booking/              # Booking templates
│   ├── core/                 # Core templates
│   ├── menu/                 # Menu templates
│   └── base.html             # Base template
├── db.sqlite3                # SQLite database
├── manage.py                 # Django management script
├── LICENSE.txt               # License file
└── README.md                 # Project documentation
```

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Run the development server: `python manage.py runserver`

## Usage

1. Access the website at http://127.0.0.1:8000/
2. Access the admin panel at http://127.0.0.1:8000/admin/
Id : aman
pass : Aman@#12
3. Use the admin panel to manage the menu, bookings, team members, testimonials, and more.

## License

This project is licensed under the terms of the license included in the repository.


page to make it more professional and industry-ready