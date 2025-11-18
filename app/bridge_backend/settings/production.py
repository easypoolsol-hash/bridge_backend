"""
Production environment settings.
Maximum security for Cloud Run deployment.
"""

import os
import re
import urllib.parse

from .base import *

# Security - Strict requirements
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required for production")

DEBUG = False  # Never debug in production

# Allowed hosts - Strict
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS environment variable is required for production")

# CORS - Strict
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

if not CORS_ALLOWED_ORIGINS:
    print("⚠️  Warning: No CORS_ALLOWED_ORIGINS set. CORS will block all origins.")

# CSRF
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# Security middleware settings
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database - PostgreSQL from Cloud SQL
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required for production")

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

# Logging - Structured JSON for Cloud Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
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
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Firebase - Initialized in base.py using FIREBASE_SERVICE_ACCOUNT_KEY from Secret Manager
# No additional configuration needed here
