import os
import djcelery

djcelery.setup_loader()

# The following settings should be overriden in your
# local_settings.py or impl_settings.py file if needed
ADD_INITIAL_DEFAULTS = {}
ADD_FORM_TARGETS = [
    ('addsame', 'I want to add another tree using the same tree details'),
    ('add', 'I want to add another tree with new details'),
    ('edit','Let me continue editing this tree'),
    ('view', "I'm done!"),
]
ADD_FORM_TARGETS_DEFAULT = 'view'
API_KEY_GOOGLE_MAP = '' # Can be empty
API_KEY_GOOGLE_ANALYTICS = 'your-key-here'

POSTAL_CODE_FIELD = "USZipCodeField"
DBH_TO_INCHES_FACTOR = 1.0

ITREE_REGION = 'NorthEast'
MULTI_REGION_ITREE_ENABLED = False

PENDING_REQUIRED_FOR_PUBLIC_EDITING_PUBLIC_TREES = False
ADVANCED_USERS_CAN_ACCEPT_PENDING = False

# Certain email servers (most, all?) prohibit traffic
# that appears to be routed from someone on the network
#
# For instance, if all mail from an OTM site is going to
# jane@company.com and jim ("jim@company.com") sends feedback
# the message structure will look like:
# From: jim@company.com
# To: jane@company.com
# ....
# But mail.company.com will *reject* the email since it is
# actually originating from otm's servers and masquerading
# as company.com
FORCE_MAIL_TO_BE_FROM = None

SHOW_ADMIN_EDITS_IN_RECENT_EDITS = False

DEBUG = True

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
    'django.contrib.markup',
    'django.contrib.flatpages',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'threadedcomments',
    'treemap',
    'api',
    'registration',
    'template_utils',
    'profiles',
    'django_reputation',
    'tagging',
    'south',
    'sorl.thumbnail',
    'classfaves',
    'qs_tiles',
    'treekey',
    'badges',
    'pagination',
    'django_sorting',
    'pipeline',
    'importer',
    'djcelery',
    'polygons'
)

try:
   from impl_settings import *
except ImportError, e:
   pass

OTM_VERSION = "1.2"
API_VERSION = "0.1"

TEMPLATE_DEBUG = DEBUG

# sorl thumbnail settings
THUMBNAIL_DEBUG = True
THUMBNAIL_SUBDIR = '_thumbs'

AUTH_PROFILE_MODULE = 'profiles.userprofile'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

ROOT_URLCONF = 'urls'

# celery config
BROKER_URL = 'redis://localhost:6379/0'

TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.load_template_source',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS += (
    #"django.core.context_processors.auth",
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'treemap.context_processors.site_root'
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.csrf.middleware.CsrfViewMiddleware',
    'django.contrib.csrf.middleware.CsrfResponseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_reputation.middleware.ReputationMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'django_sorting.middleware.SortingMiddleware',

)

try:
    from local_settings import *
except ImportError, exp:
    pass

if SITE_ROOT is not "/":
    LOGIN_URL = "%s/accounts/login" % SITE_ROOT
else:
    LOGIN_URL = "/accounts/login"
