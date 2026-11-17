"""Base settings shared by every environment. All configuration comes from the environment."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# A local .env (repo root) is optional; real environments inject variables directly.
environ.Env.read_env(BASE_DIR.parent / ".env", overwrite=False)

ENVIRONMENT = env.str("ENVIRONMENT", default="development")
SECRET_KEY = env.str("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
SITE_URL = env.str("SITE_URL", default="http://localhost:8080")
ADMIN_URL = env.str("DJANGO_ADMIN_URL", default="django-admin/")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]
THIRD_PARTY_APPS = ["rest_framework", "django_filters", "drf_spectacular", "storages"]
LOCAL_APPS = [
    "common",
    "apps.accounts",
    "apps.customers",
    "apps.categories",
    "apps.attributes",
    "apps.catalog",
    "apps.inventory",
    "apps.pricing",
    "devtools",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "common.middleware.RequestIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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
            ]
        },
    }
]

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = False
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env.str("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}}

AUTH_USER_MODEL = "accounts.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # the SPA reads it to send X-CSRFToken

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Object storage ------------------------------------------------------------
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="ecommerce-media")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="ap-south-1")
AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL", default=None)
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
MEDIA_PUBLIC_BASE_URL = env.str("MEDIA_PUBLIC_BASE_URL", default="")
STORAGES = {
    # public/ prefix is anonymously readable (bucket policy); product + campaign media live here
    "default": {"BACKEND": "common.storage.PublicMediaStorage"},
    # private/ prefix: invoices, labels, return evidence — presigned URLs only
    "private": {"BACKEND": "common.storage.PrivateMediaStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# --- DRF / OpenAPI ----------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["common.authentication.CsrfEnforcedSessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.PageNumberPagination",
    "PAGE_SIZE": 24,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "auth": env.str("THROTTLE_AUTH", default="10/min"),
        "password_reset": env.str("THROTTLE_PASSWORD_RESET", default="5/hour"),
        "search": env.str("THROTTLE_SEARCH", default="120/min"),
    },
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Commerce API",
    "DESCRIPTION": "Storefront and administration API. Money amounts are integer paise (INR).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {},
}

# --- Celery -------------------------------------------------------------------------
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_TASK_IGNORE_RESULT = True  # tasks communicate via the DB, not results
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "release-expired-reservations": {
        "task": "apps.inventory.tasks.release_expired_reservations",
        "schedule": 60.0,
    },
}

# --- Email (Django 6.1 MAILERS; provider adapters arrive with notifications in Phase 7) ----------
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": env.str("EMAIL_HOST", default="localhost"),
            "port": env.int("EMAIL_PORT", default=1025),
            "username": env.str("EMAIL_HOST_USER", default="") or None,
            "password": env.str("EMAIL_HOST_PASSWORD", default="") or None,
            "use_tls": env.bool("EMAIL_USE_TLS", default=False),
            "timeout": 10,
        },
    }
}
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="orders@localhost")

# --- Commerce ------------------------------------------------------------------------
BRAND_NAME = env.str("BRAND_NAME", default="ATELIER")
BRAND_THEME = env.str("BRAND_THEME", default="heirloom")
DEV_BRAND_NAME = "ATELIER"
ORDER_NUMBER_PREFIX = env.str("ORDER_NUMBER_PREFIX", default="AT")
SELLER_STATE_CODE = env.str("SELLER_STATE_CODE", default="27")
CHECKOUT_RESERVATION_TTL_MINUTES = env.int("CHECKOUT_RESERVATION_TTL_MINUTES", default=15)
LOW_STOCK_DISPLAY_THRESHOLD = env.int("LOW_STOCK_DISPLAY_THRESHOLD", default=3)
MAX_CART_LINE_QUANTITY = 10
PASSWORD_RESET_URL = env.str("PASSWORD_RESET_URL", default=f"{SITE_URL}/account/reset-password")

# --- Logging ---------------------------------------------------------------------------
LOG_LEVEL = env.str("LOG_LEVEL", default="INFO")
LOG_FORMAT = env.str("LOG_FORMAT", default="console")
from common.logging import build_logging_config  # noqa: E402

LOGGING = build_logging_config(level=LOG_LEVEL, fmt=LOG_FORMAT)
