from django import template

register = template.Library()

@register.filter(name='split')
def split(value, key):
    """
    Splits a string by key/delimiter and returns a list of stripped items.
    """
    if not value:
        return []
    return [item.strip() for item in value.split(key) if item.strip()]
