from django import template
register = template.Library()

def get(target_obj, attr):
    if attr:
        #if '.' in attr:
        if isinstance(target_obj,dict):
            return target_obj.get(attr)
        if hasattr(target_obj,attr):
            return getattr(target_obj,attr)
        elif target_obj.__dict__.get(attr):
            return target_obj.__dict__.get(attribute)

register.filter('get',get)