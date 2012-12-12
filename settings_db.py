DATABASES = {
    'default': {
        'NAME': 'grandrapids11',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'USER': 'phillytreemap',
        'PASSWORD': '12345',
        'HOST': '',
        'PORT': '5432',
    }
}
 

VENV_PATH = '/lib/python2.7/site-packages'

STATIC_URL = '/static/'
SITE_ROOT = '/'
MEDIA_URL = '/media/'

GEOSERVER_URL = 'http://treemap01.internal.azavea.com/geoserver/wms'
GEOSERVER_GEO_LAYER = 'gr_v11:gr_v11_trees'
GEOSERVER_GEO_STYLE = 'GR_highlight'
TILECACHE_URL = 'http://treemap01.internal.azavea.com/tilecache/'
TILECACHE_LAYER = 'GR_v11'
