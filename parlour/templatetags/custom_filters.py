from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return dictionary value for key; used in templates."""
    return dictionary.get(key)