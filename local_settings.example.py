import os

from choices import *

DATABASES = {
    'default': {
        'NAME': '{db_name}',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'USER': '{db_user}',                      # Not used with sqlite3.
        'PASSWORD': '{db_pass}',                  # Not used with sqlite3.
        'HOST': '{db_host}',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '{db_port}',
    }
}

STATIC_URL = '/static/'
FORCE_SCRIPT_NAME = ''
SITE_ROOT = '/'
MEDIA_URL = 'media/'

TILECACHE_URL = "{tc_url}"
TILECACHE_LAYER = "{tc_layer}"
TILECACHE_POLYGON_LAYER = "{tc_polygon_layer}"

GEOSERVER_GEO_LAYER = '{geo_layer}'
GEOSERVER_URL = '{geo_url}'
GEOSERVER_GEO_STYLE = "{geo_style}"

API_KEY_GOOGLE_ANALYTICS = "IGNORE"

OTM_VERSION="1.3"

SITE_LOCATION = 'New York'
COMPLETE_ARRAY = ['species','condition','sidewalk_damage','powerline_conflict_potential','canopy_height','canopy_condition','dbh','width','length','type']
REGION_NAME = 'New York'
PENDING_ON = False
MAP_CLICK_RADIUS = .0015 # in decimal degrees

BOUNDING_BOX = { # WKID 4326
    'left': -6.98318,
    'bottom': 49.864635,
    'right': 1.7689,
    'top': 58.078297
}

MAP_CENTER_LAT = 54.544
MAP_CENTER_LON = -2.79744

REPUTATION_SCORES = {
    'add tree': 25,
    'add plot': 25,
    'edit tree': 5,
    'edit plot': 5,
    'add stewardship': 5,
    'remove stewardship': -5,
    'edit verified': {
        'up': 5,
        'down': -10,
        'neutral': 1,
    },
}

EXTRAPOLATE_WITH_AVERAGE = True

#API_KEY_GOOGLE_MAP = ''
#API_KEY_GOOGLE_ANALYTICS = 'UA-23175691-1'

# pipeline minification settings
PIPELINE = False
PIPELINE_ROOT = os.path.dirname(__file__)
PIPELINE_URL = '/'
PIPELINE_YUI_BINARY = '/usr/bin/yui-compressor'
PIPELINE_YUI_JS_ARGUMENTS = '--nomunge'
PIPELINE_JS = {
    'base': {
        'source_filenames': (
            SITE_ROOT + 'static/js/jquery_mods.js',
            SITE_ROOT + 'static/treemap.js',
            SITE_ROOT + 'static/js/utils.js',
            SITE_ROOT + 'static/js/map.js',
            SITE_ROOT + 'static/js/map_init.js',
            SITE_ROOT + 'static/js/geocode.js',
            SITE_ROOT + 'static/js/page_init.js',
            SITE_ROOT + 'static/js/management.js',
            SITE_ROOT + 'static/js/comments.js',
        ),
        'output_filename': 'static/all_base.js',
    },
    'map': {
        'source_filenames': (
            SITE_ROOT + 'static/js/map.js',
            SITE_ROOT + 'static/js/threaded.js',
         ),
        'output_filename': 'static/all_map.js',
    }
}

ADMINS = (
    ('Admin1', 'you@know.who'),
)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL= 'who@are.you'
CONTACT_EMAILS = [DEFAULT_FROM_EMAIL]
EMAIL_MANAGERS = False

TILED_SEARCH_RESPONSE = False

# separate instance of tilecache for dynamic selection tiles
CACHE_SEARCH_TILES = True
CACHE_SEARCH_METHOD = 'disk' #'disk'
CACHE_SEARCH_DISK_PATH = os.path.join(os.path.dirname(__file__), 'local_tiles/')
MAPNIK_STYLESHEET = os.path.join(os.path.dirname(__file__), 'mapserver/stylesheet.xml')

CACHE_BACKEND = 'file:///tmp/trees_cache'

# django-registration
REGISTRATION_OPEN = True # defaults to True
ACCOUNT_ACTIVATION_DAYS = 5

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'


SITE_ID = 1
ROOT_URL = ""

STATIC_ROOT = '/usr/local/otm/static'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'media/')
MEDIA_URL = '/media/'
ADMIN_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'admin_media/')
ADMIN_MEDIA_PREFIX = '/admin_media/'

STATIC_DATA = os.path.join(os.path.dirname(__file__), '..', 'static/')

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'insecure'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
    '/usr/local/otm/app/templates'
)

STATICFILES_DIRS = (
    '/usr/local/otm/app/static',
)

# required keys are addsame, add, edit and view. Values and order can change. Edit tree_add view to change/add allowed keys
ADD_FORM_TARGETS = [
    ('addsame', 'I want to add another tree using the same tree details'),
    ('add', 'I want to add another tree with new details'),
    ('edit','Let me continue editing this tree'),
    ('view', 'I\'m done!'),
]

ADD_FORM_TARGETS_DEFAULT = 'view'
