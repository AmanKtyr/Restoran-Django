from django import template
import random

register = template.Library()

@register.filter(name='random_color')
def random_color(value):
    """
    Returns a random color from a predefined list based on the value
    """
    colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#fd7e14', '#6f42c1', '#20c9a6', '#5a5c69', '#858796'
    ]
    # Use the value as a seed to get consistent colors for the same value
    random.seed(value)
    return colors[value % len(colors)]

@register.filter(name='divide')
def divide(value, arg):
    """
    Divides the value by the argument
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0
