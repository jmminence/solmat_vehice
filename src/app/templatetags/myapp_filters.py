from django import template

register = template.Library()

@register.filter
def get_item(value, arg):
    try:
        return value[arg]
    except IndexError:
        return None