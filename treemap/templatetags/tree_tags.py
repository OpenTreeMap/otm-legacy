import os
import random
import posixpath
from django.conf import settings
from django.template import Library, Node
from django.db.models import get_model
     
register = Library()
     
@register.filter
def unit_or_missing(value, unit=None):
    if value:    
        if unit:
            return ("%.2f" % float(value)) + " " + unit
        return "%.2f" % float(value)
    return "Missing" 

@register.filter
def unit_or_empty(value, unit=None):
    if value:    
        if unit:
            return ("%.2f" % float(value)) + " " + unit
        return "%.2f" % float(value)
    return "" 

@register.filter
def unit_or_zero(value, unit=None):
    if value:    
        if unit:
            return ("%.2f" % float(value)) + " " + unit
        return "%.2f" % float(value)
    return "%.2f" % 0.00
