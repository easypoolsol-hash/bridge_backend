"""
Development environment settings.
For Cloud Run dev environment - uses PostgreSQL like production.
For local development on your laptop, use DJANGO_ENV=local instead.
"""

import os
import urllib.parse

from .base import *

# Security - Less strict than production for dev environment
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-DO-NOT-USE-IN-PRODUCTION")

# Debug can be enabled for dev environment
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Allowed hosts - Read from environment
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "*").split(",")
    if host.strip()
]

# CORS - Read from environment (following backend_easy pattern)
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if _cors_origins_env:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]
    CORS_ALLOW_CREDENTIALS = True
else:
    # Fallback for dev environment
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True

# CSRF - Read from environment (following backend_easy pattern)
_csrf_origins_env = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins_env.split(",") if origin.strip()]
else:
    # Fallback for dev environment
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

# Database - PostgreSQL from Cloud SQL (required for Cloud Run)
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Parse DATABASE_URL and configure PostgreSQL
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    parsed_url = urllib.parse.urlparse(DATABASE_URL)
    db_params = dict(urllib.parse.parse_qsl(parsed_url.query))

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed_url.path[1:],
            "USER": parsed_url.username,
            "PASSWORD": parsed_url.password,
            "HOST": parsed_url.hostname,
            "PORT": parsed_url.port or 5432,
            "CONN_MAX_AGE": 600,
            "OPTIONS": db_params,
        }
    }
else:
    # Fallback to SQLite if DATABASE_URL not set (backwards compatibility)
    print("⚠️  WARNING: DATABASE_URL not set. Falling back to SQLite.")
    print("⚠️  Set DJANGO_ENV=local for intentional local development.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Logging - Verbose for development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Firebase - Optional in development
# Firebase Admin SDK is initialized in base.py using FIREBASE_SERVICE_ACCOUNT_KEY env variable
# If not set, Firebase authentication will be disabled (falls back to local auth)
