import os
import random
import posixpath
from django.conf import settings
from django.template import Library, Node
from django.db.models import get_model
from treemap.views import user_is_authorized_to_update_pending_edits

register = Library()

def unit_or_expression(value, unit, failure_expression):
    """Helper function for formatting non-zero measurements

    Note that zero values will be coerced to failures to
    support legacy behavior."""
    if value:
        formatted_value = "%.2f" % float(value)
        if unit:
            formatted_value += " " + unit
        return formatted_value
    else:
        return failure_expression

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def can_approve_pending(user):
    return user_is_authorized_to_update_pending_edits(user)

@register.filter
def gal2litres(value):
    if value:
        return value * 3.78541
    else:
        return value

@register.filter
def lbs2kgs(value):
    if value:
        return value * 0.453592
    else:
        return value

@register.filter
def unit_or_missing(value, unit=None):
    return unit_or_expression(value, unit, "Missing")

@register.filter
def unit_or_empty(value, unit=None):
    return unit_or_expression(value, unit, "")

@register.filter
def unit_or_zero(value, unit=None):
    zero_expression = "%.2f" % 0.00
    return unit_or_expression(value, unit, zero_expression)

@register.filter
def unit_or_unknown(value, unit=None):
    return unit_or_expression(value, unit, "Unknown")

@register.filter
def single_quote(value):
    if value:
        return "'" + value + "'"
    else:
        return ""
