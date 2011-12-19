import os

SITE_LOCATION = 'Philadelphia'
COMPLETE_ARRAY = ['species','condition','sidewalk_damage','powerline_conflict_potential','canopy_height','canopy_condition','dbh','width','length','type']
REGION_NAME = 'Philadelphia'
PENDING_ON = False
MAP_CLICK_RADIUS = .0015 # in decimal degrees

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

DATABASES = {
    'default': {
        'NAME': 'phillytreemap',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'USER': 'phillytreemap',                      # Not used with sqlite3.
        'PASSWORD': '12345',                  # Not used with sqlite3.
        'HOST': 'sajara01',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'


SITE_ID = 1
ROOT_URL = "http://207.245.89.214"

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')
MEDIA_URL = ''
ADMIN_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'admin_media/')
ADMIN_MEDIA_PREFIX = '/admin_media/'

STATIC_DATA = os.path.join(os.path.dirname(__file__), 'static/')

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'insecure'


TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates/Philadelphia'),
    os.path.join(os.path.dirname(__file__), 'templates'),
)


