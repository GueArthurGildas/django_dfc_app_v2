from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """Retourne la valeur absolue d'un nombre."""
    try:
        return abs(int(value))
    except (TypeError, ValueError):
        return value

@register.filter
def subtract(value, arg):
    """Soustrait arg de value."""
    try:
        return int(value) - int(arg)
    except (TypeError, ValueError):
        return value
