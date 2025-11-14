"""
Base settings shared across all environments.
Following Fortune 500 / Google Cloud best practices.
"""

import os
import re
import urllib.parse
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent


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
    "django_filters",  # API filtering
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


# Custom User Model
AUTH_USER_MODEL = "accounts.User"


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# File Storage Configuration
# Use GCS for production, local storage for development
import os
USE_GCS_STORAGE = os.environ.get('USE_GCS_STORAGE', 'false').lower() == 'true'

if USE_GCS_STORAGE:
    # Google Cloud Storage for production
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'bridge-lead-pdfs')
    print(f"[STORAGE] Using GCS storage: {GCS_BUCKET_NAME}")

    STORAGES = {
        "default": {
            "BACKEND": "bridge_backend.storage.GoogleCloudStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    # Local file storage for development
    print("[STORAGE] Using local file storage")

    STORAGES = {
        "default": {
            "BACKEND": "bridge_backend.storage.LocalFileStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "bridge_backend.core.authentication.FirebaseAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # API uses token auth (Firebase JWT), not sessions - CSRF not needed
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}


# DRF Spectacular (OpenAPI) settings
SPECTACULAR_SETTINGS = {
    "TITLE": "EasyPool Bridge API",
    "DESCRIPTION": "Agent management system for insurance leads collection",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [{"FirebaseAuth": []}],
    "SECURITY_DEFINITIONS": {
        "FirebaseAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Firebase ID Token. Get it from Firebase Authentication.",
        }
    },
}


# Firebase Admin SDK Initialization
# Following backend_easy pattern - initialize at settings load time
try:
    import json
    import firebase_admin
    from firebase_admin import credentials

    _firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
    if _firebase_key and not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(_firebase_key))
        firebase_admin.initialize_app(cred)
        print("[FIREBASE] Firebase Admin initialized successfully")
    elif not _firebase_key:
        print("[FIREBASE] FIREBASE_SERVICE_ACCOUNT_KEY not set - Firebase auth will not work")
except (ImportError, ValueError, KeyError) as e:
    print(f"[FIREBASE] Firebase initialization failed: {e}")
    pass  # Firebase optional in local/CI environments
