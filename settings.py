import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

#local_settings
GOOGLE_API_KEY = 'abcdf'
GOOGLE_API_DEV_KEY = 'ghijk'

# must end with trees/ because of odd tilecache deployment issue
# will be populated with layer name /trees/{layername} dynamically
# in javascript depending on the google base layer being used
TC_URL = 'http://tilecache.urbanforestmap.org/tiles/1.0.0/trees/'

STATIC_DATA = os.path.join(os.path.dirname(__file__), 'static/')

ADMINS = (
    ('Admin1', 'josh@umbrellaconsulting.com'),
)

ROOT_URL = 'http://urbanforestmap.org'

TILED_SEARCH_RESPONSE = True

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

AUTH_PROFILE_MODULE = 'profiles.userprofile'

MANAGERS = ADMINS

# django-registration
REGISTRATION_OPEN = True # defaults to True
ACCOUNT_ACTIVATION_DAYS = 5

DEFAULT_FROM_EMAIL= 'contact@urbanforestmap.org'
EMAIL_MANAGERS = False

EMAIL_HOST = 'postoffice.dca.net'
EMAIL_PORT = 25

#reputation
REPUTATION_ENABLED = True
MAX_REPUTATION_LOSS_PER_DAY = 100
BASE_REPUTATION = 0
REPUTATION_REQUIRED_TEMPLATE = 'django_reputation/reputation_required.html'
MAX_REPUTATION_GAIN_PER_DAY = 100


#http://sftrees.securemaps.com/ticket/236
CONTACT_EMAILS = ['kelaine@urbanforestmap.org','josh@umbrellaconsulting.com']#,'admins@urbanforestmap.org']

CACHE_BACKEND = 'file:///tmp/trees_cache'

DATABASES = {
    'default': {
        'NAME': 'sftrees',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'USER': 'treekeyuser',                      # Not used with sqlite3.
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
TIME_ZONE = 'America/Vancouver'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'insecure'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',

#     'django.template.loaders.eggs.load_template_source',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS += (
     'django.core.context_processors.request',
     'global_context.gkey',
     'global_context.tc_url',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.csrf.middleware.CsrfViewMiddleware',
    'django.contrib.csrf.middleware.CsrfResponseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django_reputation.middleware.ReputationMiddleware'
    #'middleware.ajax.AJAXSimpleExceptionResponse',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.databrowse',
    'django.contrib.gis',
    'django.contrib.humanize',
    'django.contrib.webdesign',
    'django.contrib.comments',
    'django.contrib.markup',
    'django.contrib.flatpages',
    'treemap',
    'registration',
    'template_utils',
    'profiles',
    'django_reputation',
    'tagging',
    'sorl.thumbnail',
    'classfaves',
    'qs_tiles',
    'treekey',
)

try:
    from local_settings import *
except ImportError, exp:
    pass
