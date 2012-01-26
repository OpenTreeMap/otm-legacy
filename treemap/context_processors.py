from django.conf import settings

def site_root(context):
    return {
        'SITE_ROOT': settings.SITE_ROOT,
        'GEOSERVER_URL': settings.GEOSERVER_URL,
        'TILECACHE_URL': settings.TILECACHE_URL,
        'TILECACHE_LAYER': settings.TILECACHE_LAYER }
