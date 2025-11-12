"""
Django settings for bridge_backend project.

Production-ready settings that read from environment variables.
Following 12-factor app methodology and Fortune 500 best practices.
"""

import os
import re
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


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Custom apps
    "accounts",
    "products",
    "leads",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Google Cloud Run best practice
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
    # Parse DATABASE_URL for Cloud SQL or standard PostgreSQL
    if "?host=/cloudsql/" in DATABASE_URL or "@//cloudsql/" in DATABASE_URL:
        # Cloud SQL Unix socket format
        if "?host=/cloudsql/" in DATABASE_URL:
            match = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@/([^?]+)\?host=(.+)", DATABASE_URL)
            if match:
                user, password, dbname, host = match.groups()
            else:
                raise ValueError(f"Invalid Cloud SQL DATABASE_URL format: {DATABASE_URL}")
        else:
            match = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@//cloudsql/([^/]+)/(.+)", DATABASE_URL)
            if match:
                user, password, instance, dbname = match.groups()
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
            raise ValueError(f"Invalid DATABASE_URL format: {DATABASE_URL}")
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
