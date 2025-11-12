"""
Development environment settings.
Optimized for local development with relaxed security.
"""

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-dev-key-DO-NOT-USE-IN-PRODUCTION"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# CORS - Read from environment (following backend_easy pattern)
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if _cors_origins_env:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]
    CORS_ALLOW_CREDENTIALS = True
else:
    # Fallback for local development
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True

# CSRF - Read from environment (following backend_easy pattern)
_csrf_origins_env = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins_env.split(",") if origin.strip()]
else:
    # Fallback for local development
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

# Database - SQLite for local development
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

# Firebase - Optional in development (falls back to local auth)
# If you want to test Firebase, set FIREBASE_CREDENTIALS_PATH env variable
if not FIREBASE_CREDENTIALS_PATH:
    print("⚠️  Warning: FIREBASE_CREDENTIALS_PATH not set. Firebase authentication disabled for development.")
