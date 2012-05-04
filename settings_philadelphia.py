import os


OTM_VERSION="1.1"

SITE_LOCATION = 'Philadelphia'
COMPLETE_ARRAY = ['species','condition','sidewalk_damage','powerline_conflict_potential','canopy_height','canopy_condition','dbh','width','length','type']
REGION_NAME = 'Philadelphia'
PENDING_ON = False
MAP_CLICK_RADIUS = .0015 # in decimal degrees

# pipeline minification settings
PIPELINE = False
PIPELINE_ROOT = os.path.dirname(__file__)
PIPELINE_URL = '/'
PIPELINE_YUI_BINARY = '/usr/bin/yui-compressor'
PIPELINE_YUI_JS_ARGUMENTS = '--nomunge'
PIPELINE_JS = {
    'base': {
        'source_filenames': (
            'static/js/jquery_mods.js',
	    'static/treemap.js',
            'static/js/utils.js',
            'static/js/map_init.js',
            'static/js/geocode.js',
            'static/js/page_init.js',
            'static/js/management.js',
            'static/js/comments.js',
        ),
        'output_filename': 'static/all_base.js',
    },
    'map': {
        'source_filenames': (
            'static/js/Philadelphia/map.js',
            'static/js/Philadelphia/threaded.js',
        ),
        'output_filename': 'static/all_map.js',
    }

}
# PIPELINE_CSS = {
#     'all': {
# 	'source_filenames': (
# 	    'static/css/DCTreekit/treemap.css',
# 	    'static/css/DCTreekit/ptm.css'
# 	),
#         'output_filename': 'static/all.css',
#     }
# }

ADMINS = (
    ('Admin1', 'cbrittain@azavea.com'),
)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL= 'contact@phillytreemap.org'
CONTACT_EMAILS = ['phillytreemap@pennhort.org']
EMAIL_MANAGERS = False

EMAIL_HOST = 'postoffice.dca.net'
EMAIL_PORT = 25

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
ROOT_URL = "http://207.245.89.214"

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')
MEDIA_URL = '/media/'
ADMIN_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'admin_media/')
ADMIN_MEDIA_PREFIX = '/admin_media/'

STATIC_DATA = os.path.join(os.path.dirname(__file__), 'static/')

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'insecure'


TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates/Philadelphia'),
    os.path.join(os.path.dirname(__file__), 'templates'),
)

try:
    from settings_db import *
except ImportError, exp:
    pass


