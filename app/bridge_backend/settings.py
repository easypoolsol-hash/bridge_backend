"""
Django settings for bridge_backend project.

Production-ready settings that read from environment variables.
Following 12-factor app methodology and Fortune 500 best practices.
"""

import os
import re
import urllib.parse
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY: Read from environment variables (injected by Cloud Run/Terraform)
# See: terragrunt/live/dev/backend-service/terragrunt.hcl for configuration

# SECRET_KEY from environment (required for security)
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-l=6tbx1=_6_28dg(!1+nwqpjd697fcva65q1sr=zl7ayw!8t!z")

# DEBUG from environment (default: False for production)
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ALLOWED_HOSTS from environment (required for security)
# Terraform/Cloud Run injects the correct Cloud Run URL
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

# CSRF Protection - Fortune 500 / Google Cloud best practice
# Read from environment variable injected by Terraform/Cloud Run
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]

# CORS Configuration - Fortune 500 / Google Cloud best practice
# Read from environment variable injected by Terraform/Cloud Run
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()]

# Development: Allow localhost origins for Flutter web testing
if DEBUG:
    CORS_ALLOWED_ORIGINS.extend([
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8083",
        "http://localhost:8084",
    ])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "drf_spectacular",  # OpenAPI 3 schema generation
    "corsheaders",
    # Custom apps
    "accounts",
    "products",
    "leads",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Google Cloud Run best practice
    "corsheaders.middleware.CorsMiddleware",  # CORS must be before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bridge_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "bridge_backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# Production: Uses DATABASE_URL from environment (injected by Terraform/Secret Manager)
# Local: Falls back to SQLite for development

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Check for SQLite URL (for testing)
    if DATABASE_URL.startswith("sqlite://"):
        sqlite_path = DATABASE_URL.replace("sqlite://", "")
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": sqlite_path,
            }
        }
    # Parse DATABASE_URL for Cloud SQL or standard PostgreSQL
    elif "?host=/cloudsql/" in DATABASE_URL or "@//cloudsql/" in DATABASE_URL:
        # Cloud SQL Unix socket format
        if "?host=/cloudsql/" in DATABASE_URL:
            match = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@/([^?]+)\?host=(.+)", DATABASE_URL)
            if match:
                user, password, dbname, host = match.groups()
                password = urllib.parse.unquote(password)  # URL-decode password
            else:
                raise ValueError(f"Invalid Cloud SQL DATABASE_URL format: {DATABASE_URL}")
        else:
            match = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@//cloudsql/([^/]+)/(.+)", DATABASE_URL)
            if match:
                user, password, instance, dbname = match.groups()
                password = urllib.parse.unquote(password)  # URL-decode password
                host = f"/cloudsql/{instance}"
            else:
                raise ValueError(f"Invalid Cloud SQL DATABASE_URL format: {DATABASE_URL}")

        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": dbname,
                "USER": user,
                "PASSWORD": password,
                "HOST": host,
                "OPTIONS": {
                    "connect_timeout": 10,
                    "options": "-c timezone=UTC",
                },
                "CONN_MAX_AGE": 60,
                "CONN_HEALTH_CHECKS": True,
            }
        }
    else:
        # Standard PostgreSQL URL format
        match = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:]+):?(\d+)?/(.+)", DATABASE_URL)
        if match:
            user, password, host, port, dbname = match.groups()
            password = urllib.parse.unquote(password)  # URL-decode password
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": dbname,
                    "USER": user,
                    "PASSWORD": password,
                    "HOST": host,
                    "PORT": port or "5432",
                    "OPTIONS": {
                        "connect_timeout": 10,
                        "options": "-c timezone=UTC",
                    },
                    "CONN_MAX_AGE": 60,
                    "CONN_HEALTH_CHECKS": True,
                }
            }
        else:
            # Fallback: treat as SQLite if regex doesn't match
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": "/tmp/db.sqlite3",
                }
            }
else:
    # Fallback to SQLite for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
# Google Cloud Run Best Practice: Use WhiteNoise for static file serving

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise configuration (Fortune 500 best practices)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# WhiteNoise: Enable compression and caching
WHITENOISE_KEEP_ONLY_HASHED_FILES = True
WHITENOISE_MANIFEST_STRICT = False  # Avoid errors in development

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# ==============================================================================
# REST FRAMEWORK CONFIGURATION
# ==============================================================================

REST_FRAMEWORK = {
    # Authentication
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "bridge_backend.core.authentication.FirebaseAuthentication",  # Firebase JWT tokens
        "rest_framework.authentication.SessionAuthentication",  # Django admin/browsable API
    ],
    # Permissions (secure by default)
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",  # Require authentication for all endpoints
    ],
    # Pagination
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Renderers
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  # Only in DEBUG mode
    ],
    # Throttling (protect against abuse)
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    # OpenAPI schema (drf-spectacular)
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ==============================================================================
# DRF-SPECTACULAR CONFIGURATION (OpenAPI 3.0 Schema Generation)
# Google/Fortune 500 Best Practice: Auto-generated API documentation
# ==============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "EasyPool Bridge API",
    "DESCRIPTION": "Agent management system for insurance, loans, credit cards, and investments",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Authentication
    "SECURITY": [{"FirebaseAuth": []}],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "FirebaseAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Firebase ID token obtained from Firebase Authentication",
            }
        }
    },
    # Schema generation
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/",
    # Enum behavior
    "ENUM_NAME_OVERRIDES": {
        "StatusEnum": "leads.models.Lead.STATUS_CHOICES",
    },
}

# ==============================================================================
# FIREBASE ADMIN SDK CONFIGURATION
# ==============================================================================

import firebase_admin
from firebase_admin import credentials

# Initialize Firebase Admin SDK
# Service account key is injected via Secret Manager in Cloud Run
FIREBASE_SERVICE_ACCOUNT_KEY = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")

if FIREBASE_SERVICE_ACCOUNT_KEY:
    try:
        import json

        cred_dict = json.loads(FIREBASE_SERVICE_ACCOUNT_KEY)
        cred = credentials.Certificate(cred_dict)

        # Only initialize if not already initialized
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
elif DEBUG:
    # Development mode: Firebase optional (use session auth for admin panel)
    import logging

    logger = logging.getLogger(__name__)
    logger.warning("Firebase Admin SDK not initialized (FIREBASE_SERVICE_ACCOUNT_KEY not set)")
