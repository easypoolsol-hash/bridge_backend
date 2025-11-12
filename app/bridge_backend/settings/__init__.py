"""
Settings module with automatic environment detection.
Following Fortune 500 / Google Cloud best practices.

Environment detection order:
1. DJANGO_ENV environment variable (explicit)
2. Cloud Run environment detection (K_SERVICE)
3. Development (default)
"""

import os

# Detect environment
DJANGO_ENV = os.getenv("DJANGO_ENV")

if DJANGO_ENV:
    # Explicit environment override
    env = DJANGO_ENV
elif os.getenv("K_SERVICE"):
    # Running on Cloud Run
    env = "production"
else:
    # Local development
    env = "development"

print(f"🔧 Loading settings for environment: {env}")

# Import the appropriate settings
if env == "production":
    from .production import *
elif env == "staging":
    from .staging import *
else:
    from .development import *
