from django import template

register = template.Library()

@register.filter
def filesizeformat(value):
    if value is None:
        return "0 bytes"  # or another suitable default representation
    if value < 1024:
        return f'{value} bytes'
    elif value < 1048576:
        return f'{value/1024:.2f} KB'
    elif value < 1073741824:
        return f'{value/1048576:.2f} MB'
    else:
        return f'{value/1073741824:.1f} GB'

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None  # Return None or handle the case when the first argument is not a dictionary
