from django import template
register = template.Library()

def float_add(value, arg):
    "adds the arg and the value"
    return value + arg

def mult(value, arg):
    "Multiplies the arg and the value"
    return int(value) * int(arg)

def sub(value, arg):
    "Subtracts the arg from the value"
    return int(value) - int(arg)

def div(value, arg):
    "Divides the value by the arg"
    return int(value) / int(arg)

register.filter('mult', mult)
register.filter('sub', sub)
register.filter('div', div)
register.filter('float_add', float_add)
