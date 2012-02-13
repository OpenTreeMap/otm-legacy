from treemap.models import CommentFlag
from django import template

register = template.Library()

@register.filter
def is_flagged(comment, user):
    return len(CommentFlag.objects.filter(user=user, comment=comment)) > 0
