import os

SITE_LOCATION = 'SanFrancisco'
PENDING_ON = False
REGION_NAME = 'Greenprint'
#local_settings
GOOGLE_API_KEY = 'abcdf'

COMPLETE_ARRAY = ['species','condition','sidewalk_damage','powerline_conflict_potential','dbh','plot_width','plot_length','plot_type']
MAP_CLICK_RADIUS = .0015 # in decimal degrees
        

# must end with trees/ because of odd tilecache deployment issue
# will be populated with layer name /trees/{layername} dynamically
# in javascript depending on the google base layer being used
TC_URL = 'http://tilecache.urbanforestmap.org/tiles/1.0.0/trees/'

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

