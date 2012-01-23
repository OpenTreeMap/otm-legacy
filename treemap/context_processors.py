from django.conf import settings

def site_root(context):
    return {'SITE_ROOT': settings.SITE_ROOT }
