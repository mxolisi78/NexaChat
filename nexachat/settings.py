"""
Django settings for nexachat project.
"""

from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------------------------------------------
# Security
# -------------------------------------------------------------------
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-change-in-prod')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())


# -------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'chat',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nexachat.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nexachat.wsgi.application'
ASGI_APPLICATION = 'nexachat.asgi.application'


# -------------------------------------------------------------------
# Database
# -------------------------------------------------------------------
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# -------------------------------------------------------------------
# Password validation
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# -------------------------------------------------------------------
# i18n
# -------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# -------------------------------------------------------------------
# Static + Media
# -------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# -------------------------------------------------------------------
# Email (dev)
# -------------------------------------------------------------------
MAILERS = {
    'default': {'BACKEND': 'django.core.mail.backends.console.EmailBackend'},
}


# -------------------------------------------------------------------
# Channels + Redis
# -------------------------------------------------------------------
REDIS_URL = config('REDIS_URL', default='')

if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [{
                    'address': REDIS_URL,
                    'socket_connect_timeout': 10,
                    'socket_timeout': 30,
                    'retry_on_timeout': True,
                    'health_check_interval': 30,
                }],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
    }


# -------------------------------------------------------------------
# REST Framework
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# -------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]


# -------------------------------------------------------------------
# Auth redirects
# -------------------------------------------------------------------
LOGIN_URL = 'chat:login'
LOGIN_REDIRECT_URL = 'chat:dashboard'
LOGOUT_REDIRECT_URL = 'chat:home'


# -------------------------------------------------------------------
# Third-party keys
# -------------------------------------------------------------------
GNEWS_API_KEY = config('GNEWS_API_KEY', default='')


# -------------------------------------------------------------------
# Production security (only when DEBUG=False)
# -------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


# -------------------------------------------------------------------
# ALLOWED_HOSTS — always allow onrender.com in prod
# -------------------------------------------------------------------
if '.onrender.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS) + ['.onrender.com']


# -------------------------------------------------------------------
# CSRF_TRUSTED_ORIGINS — dev + prod (defined once)
# -------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://*.onrender.com',
    'https://nexachat-9cfg.onrender.com',
]

# Merge extra origins from env if present
extra_origins = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
for origin in extra_origins:
    if origin and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)


# -------------------------------------------------------------------
# Default primary key
# -------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'