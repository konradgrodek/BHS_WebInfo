"""
Django settings for BHS_Info project.

Generated by 'django-admin startproject' using Django 3.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
with open(Path(__file__).resolve().parent.joinpath('.secret'), 'r') as secret_file:
     SECRET_KEY = secret_file.read()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if sys.gettrace() else False

ALLOWED_HOSTS = [
    '192.168.1.5',
    '192.168.1.6',
    'info.home.online',
    'red.home.online',
    'home.online'
]


# Application definition

INSTALLED_APPS = [
    'info.apps.InfoConfig',
    'django.contrib.staticfiles',
    'mod_wsgi.server'
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'BHS_Info.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'BHS_Info.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'pl-pl'

TIME_ZONE = 'Poland'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = './static' if DEBUG else '/usr/local/bin/web-info/static'
