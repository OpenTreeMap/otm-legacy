import os

SITE_LOCATION = 'SanFrancisco'
PENDING_ON = False
REGION_NAME = 'Greenprint'
#local_settings

#API_KEY_GOOGLE_MAP = 'AIzaSyCI-d2nJPOKOJnatoN02r9_fan8ULt6TWI'
API_KEY_GOOGLE_MAP = ''
API_KEY_GOOGLE_ANALYTICS = 'UA-13228685-1'

COMPLETE_ARRAY = ['species','condition','sidewalk_damage','powerline_conflict_potential','dbh','width','length','type']
MAP_CLICK_RADIUS = .0015 # in decimal degrees
        
EXTRAPOLATE_WITH_AVERAGE = True

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
            'static/js/SanFrancisco/map.js',
            'static/js/SanFrancisco/threaded.js',
        ),
        'output_filename': 'static/all_map.js',
    }

}


STATIC_DATA = os.path.join(os.path.dirname(__file__), 'static/')

ADMINS = (
    ('Admin1', 'cbrittain@azavea.com'),
)

ROOT_URL = 'http://urbanforestmap.org'

TILED_SEARCH_RESPONSE = False

# separate instance of tilecache for dynamic selection tiles
CACHE_SEARCH_TILES = True
CACHE_SEARCH_METHOD = 'disk' #'disk'
CACHE_SEARCH_DISK_PATH = os.path.join(os.path.dirname(__file__), 'local_tiles/')
MAPNIK_STYLESHEET = os.path.join(os.path.dirname(__file__), 'mapserver/stylesheet.xml')

# sorl thumbnail settings
THUMBNAIL_DEBUG = True
THUMBNAIL_SUBDIR = '_thumbs'
#THUMBNAIL_EXTENSION = 'png'
#THUMBNAIL_QUALITY = 95 # if not using png

MANAGERS = ADMINS

# django-registration
REGISTRATION_OPEN = True # defaults to True
ACCOUNT_ACTIVATION_DAYS = 5

DEFAULT_FROM_EMAIL= 'contact@urbanforestmap.org'
EMAIL_MANAGERS = False

#http://sftrees.securemaps.com/ticket/236
CONTACT_EMAILS = ['cbrittain@azavea.com']#,'admins@urbanforestmap.org']

CACHE_BACKEND = 'file:///tmp/trees_cache'


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Vancouver'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'
ADMIN_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'admin_media/')

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'insecure'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates/SanFrancisco'),
    os.path.join(os.path.dirname(__file__), 'templates'),
)

from settings_db import *

