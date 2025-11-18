"""
Staging environment settings.
Production-like but with relaxed CORS for testing.
"""

import os
import re
import urllib.parse

from .base import *

# Security
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required for staging")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Allowed hosts
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# CORS - Read from environment with fallback for testing
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Add localhost for staging testing
CORS_ALLOWED_ORIGINS.extend([
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082",
    "http://localhost:8083",
    "http://localhost:8084",
])

# CSRF
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# Database - PostgreSQL from Cloud SQL
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required for staging")

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

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
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
}

# Firebase - Initialized in base.py using FIREBASE_SERVICE_ACCOUNT_KEY from Secret Manager
# No additional configuration needed here
