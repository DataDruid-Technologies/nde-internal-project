# In your app directory (e.g., core/templatetags/custom_filters.py)

from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter(name='abs')
def abs_filter(value):
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter(name='percentage')
def percentage(value, decimal_places=1):
    try:
        formatted_value = floatformat(abs(float(value)), decimal_places)
        return f"{formatted_value}%"
    except (ValueError, TypeError):
        return value