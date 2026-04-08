import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from dotenv import load_dotenv

load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = True
print(f"DEBUG: {DEBUG}")
RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")

CSRF_TRUSTED_ORIGINS = [f"https://{RAILWAY_PUBLIC_DOMAIN}"]
ALLOWED_HOSTS = ["*"]
# ALLOWED_HOSTS = [
#     "localhost",
#     "127.0.0.1",
#     RAILWAY_PUBLIC_DOMAIN
# ]
DRAFT = True
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "channels",
    "rest_framework",
    "apps.accounts",
    "apps.lists",
    "apps.dictionary",
    "apps.study",
    "apps.social",
    "apps.ingestion",
    "apps.video",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

ASGI_APPLICATION = "config.asgi.application"

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

CELERY_BROKER_URL = os.getenv("REDIS_URL")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL")

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DB_ENGINE = os.environ.get("DJANGO_DB")
if DB_ENGINE == "postgres":
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ.get("DATABASE_URL"), conn_max_age=600, ssl_require=True
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
        "parsed": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "parsed_words_berries.db",  # база парсера
        },
    }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", BASE_DIR / "media")
# MEDIA_ROOT = "/var/www/media"

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",  # для глобального static/
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "none"  # для старта

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

SPACY_MODEL = "en_core_web_sm"

# CELERY_BROKER_URL = "redis://localhost:6379/0"  # URL брокера сообщений
# if os.environ.get('DEBUG') == 'True' or os.environ.get('ENV') == 'local':
#     CELERY_BROKER_URL = 'redis://localhost:6379/0'
# else:
#     CELERY_BROKER_URL = os.environ.get('REDIS_URL') or os.environ.get('CELERY_BROKER_URL')
#
# CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
SUBTITLE_PREVIEW_TTL = 3600
