from datetime import timedelta
from pathlib import Path

import environ


env = environ.Env()
environ.Env.read_env(".env")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")
RANDOM_SEED = 50

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if env("DJANGO_DEBUG") == "True" else False
ADMIN_ENABLED = False

DOMAIN = env("DOMAIN", default=None)
FRONT_END_DOMAIN = env("FRONT_END_DOMAIN", default=None)

if DEBUG:
    ALLOWED_HOSTS = ["*"]
    CORS_ALLOW_ALL_ORIGINS = True  # for vue
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    CSRF_TRUSTED_ORIGINS = ["https://*.127.0.0.1", "https://*.localhost"]
    if DOMAIN:
        ALLOWED_HOSTS.append(DOMAIN)
        CSRF_TRUSTED_ORIGINS.append(f"https://{DOMAIN}")
    if FRONT_END_DOMAIN:
        ALLOWED_HOSTS.append(FRONT_END_DOMAIN)
        CSRF_TRUSTED_ORIGINS.append(f"https://{FRONT_END_DOMAIN}")
 
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

INTERNAL_IPS = [
    "127.0.0.1",
]

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "corsheaders",
    "django_filters",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_yasg",
    "django_q",
    "main",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATIC_URL = "static/"

ROOT_URLCONF = "PatentInspector.urls"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}
SWAGGER_SETTINGS = {
    "DEFAULT_AUTO_SCHEMA_CLASS": "main.schema.ReadWriteAutoSchema",
    "USE_SESSION_AUTH": False,
    "SECURITY_DEFINITIONS": {
        "DRF Token": {"type": "apiKey", "name": "Authorization", "in": "header"},
    },
    "PERSIST_AUTH": True,
}

AUTH_USER_MODEL = "main.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "PatentInspector.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST") if DEBUG else "postgres",
        "PORT": env("POSTGRES_PORT"),
        "CONN_MAX_AGE": 300 # 5 minutes,
    }
}

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True
USE_THOUSAND_SEPARATOR = True


# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django Q
Q_CLUSTER = {
    "name": "PatentInspector",
    "orm": "default",
    "timeout": env.int("DJANGO_Q_TIMEOUT"), 
    "retry": env.int("DJANGO_Q_RETRY"),
    "max_attempts": env.int("DJANGO_Q_MAX_ATTEMPTS"),
    "save_limit": env.int("DJANGO_Q_SAVE_LIMIT"),
    "workers": env.int("DJANGO_Q_WORKERS"),
}

# Email configuration
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

# Performance settings
MAX_PATENTS_PER_REPORT = env.int("MAX_PATENTS_PER_REPORT")