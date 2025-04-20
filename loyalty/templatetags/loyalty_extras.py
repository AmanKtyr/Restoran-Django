from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return value
    
@register.filter
def percentage(value, arg):
    """Calculate percentage of value to arg."""
    try:
        return int((float(value) / float(arg)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
    
@register.filter
def special_benefits_list(value):
    """Convert special benefits text to a list."""
    if not value:
        return []
    return [benefit.strip() for benefit in value.split('\n') if benefit.strip()]
