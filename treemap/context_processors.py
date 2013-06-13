from django.conf import settings

def site_root(context):
    return {
        'GEOSERVER_GEO_LAYER': settings.GEOSERVER_GEO_LAYER,
        'GEOSERVER_GEO_STYLE': settings.GEOSERVER_GEO_STYLE,
        'SITE_ROOT': settings.SITE_ROOT,
        'GEOSERVER_URL': settings.GEOSERVER_URL,
        'TILECACHE_URL': settings.TILECACHE_URL,
        'TILECACHE_LAYER': settings.TILECACHE_LAYER,
        'TILECACHE_POLYGON_LAYER': settings.TILECACHE_POLYGON_LAYER,
        'API_KEY_GOOGLE_MAP': settings.API_KEY_GOOGLE_MAP,
        'API_KEY_GOOGLE_ANALYTICS': settings.API_KEY_GOOGLE_ANALYTICS
    }
