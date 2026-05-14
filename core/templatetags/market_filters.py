# core/templatetags/market_filters.py
from django import template

register = template.Library()

@register.filter
def max_value(lst):
    if lst and len(lst) > 0:
        return max(lst)
    return 0

@register.filter
def min_value(lst):
    if lst and len(lst) > 0:
        return min(lst)
    return 0

@register.filter
def avg_value(lst):
    if lst and len(lst) > 0:
        return sum(lst) / len(lst)
    return 0



@register.filter
def splitlines(value):
    """Split string into lines"""
    if value:
        return value.splitlines()
    return []

@register.filter
def startswith(value, arg):
    """Check if string starts with arg"""
    if value and arg:
        return value.startswith(arg)
    return False