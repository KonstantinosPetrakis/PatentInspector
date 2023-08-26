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

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if env("DJANGO_DEBUG") == "True" else False

if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    CSRF_TRUSTED_ORIGINS = ["https://*.127.0.0.1", "https://*.localhost"]
    if DOMAIN := env("DOMAIN", default=None):
        ALLOWED_HOSTS.append(DOMAIN)
        CSRF_TRUSTED_ORIGINS.append(f"https://{DOMAIN}")
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
    'django.contrib.auth',
    'main',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'admin_reorder',
    'leaflet',
    # 'debug_toolbar',
    'macros'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'admin_reorder.middleware.ModelAdminReorder',
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = 'PatentAnalyzer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'PatentAnalyzer.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST") if DEBUG else "postgres",
        "PORT": env("POSTGRES_PORT"),
        "CONN_MAX_AGE": 600, # 10 minutes
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True
USE_THOUSAND_SEPARATOR = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Custom apps configuration
RANDOM_SEED = 42

# Restrict heavy operations based on if the app runs locally or on the server (has a domain)
DEPLOYED = bool(env("DOMAIN", default=None))

# Leaflet
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (44.638569, -63.586262),
    'DEFAULT_ZOOM': 18,
    'MAX_ZOOM': 20,
    'MIN_ZOOM': 3,
    'SCALE': 'both',
    'ATTRIBUTION_PREFIX': 'Location Tracker'
}

# ModelAdmin-Reorder
ADMIN_REORDER = (
    {'app': 'main', 'label': 'Patent related', 'models': (
        {'model': 'main.Patent',         'label': 'Patents'},
        {'model': 'main.PatentCitation', 'label': 'Patent Citation'},
        {'model': 'main.Location',       'label': 'Locations'},
        {'model': 'main.Inventor',       'label': 'Inventor'},
        {'model': 'main.Assignee',       'label': 'Assignee'},
    )}, 
    {'app': 'main', 'label': 'CPC related', 'models': (
        {'model': 'main.CPCSection',     'label': 'Sections'},
        {'model': 'main.CPCClass',       'label': 'Classes'},
        {'model': 'main.CPCSubclass',    'label': 'Subclasses'},
        {'model': 'main.CPCGroup',       'label': 'Groups'},
    )}
)

# DEBUG_TOOLBAR_CONFIG = {
#     "PROFILER_THRESHOLD_RATIO": 500
# }