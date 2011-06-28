import os
import random
import posixpath
from django.conf import settings
from django.template import Library, Node
from django.db.models import get_model
     
register = Library()
     
class LatestContentNode(Node):
    def __init__(self, model, num, varname):
        self.num, self.varname = num, varname
        self.model = get_model(*model.split('.'))
    
    def render(self, context):
        context[self.varname] = self.model._default_manager.all().order_by('-date_created')[:self.num]
        return ''
 
def get_latest(parser, token):
    bits = token.contents.split()
    if len(bits) != 5:
        raise TemplateSyntaxError, "get_latest tag takes exactly four arguments"
    if bits[3] != 'as':
        raise TemplateSyntaxError, "third argument to get_latest tag must be 'as'"
    res = LatestContentNode(bits[1], bits[2], bits[4])
    return res

get_latest = register.tag(get_latest)



@register.filter
def truncatewords_by_chars(value, arg):
  """
  Truncate words based on the number of characters
  based on original truncatewords filter code
  
  Receives a parameter separated by spaces where each field means:
   - limit: number of characters after which the string is truncated
   - lower bound: if char number is higher than limit, truncate by lower bound
   - higher bound: if char number is less than limit, truncate by higher bound
  """
  from django.utils.text import truncate_words
  try:
    args = arg.split(' ')
    limit = int(args[0])
    lower = int(args[1])
    higher = int(args[2])
  except ValueError: # Invalid literal for int().
    return value
  if len(value) >= limit:
    return truncate_words(value, lower)
  if len(value) < limit:
    return truncate_words(value, higher)

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
