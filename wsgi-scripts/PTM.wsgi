import os, sys

# Redirect stdout to stderr to avoid annoying crashes
sys.stdout = sys.stderr

sys.path.insert(0, '/home/azavea/UrbanForestMap')

main_path = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
sys.path.insert(0, main_path)

import settings
import site

if hasattr(settings,"VENV_PATH") and settings.VENV_PATH:
    site.addsitedir(settings.VENV_PATH)

import django.core.management
django.core.management.setup_environ(settings)
utility = django.core.management.ManagementUtility()
command = utility.fetch_command('runserver')

command.validate()

import django.conf
import django.utils

django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()


