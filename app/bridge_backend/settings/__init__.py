"""
Settings module with automatic environment detection.
Following Fortune 500 / Google Cloud best practices.

Supported environments:
- production: Cloud Run production (PostgreSQL, strict security)
- staging: Cloud Run staging (PostgreSQL, relaxed security)
- development: Cloud Run dev (PostgreSQL, DEBUG=True, relaxed security)
- local: Local laptop development (SQLite, no PostgreSQL needed)

Environment detection order:
1. DJANGO_ENV environment variable (explicit override)
2. Cloud Run auto-detection (K_SERVICE → production)
3. Local development (default → local)
"""

import os

# Detect environment
DJANGO_ENV = os.getenv("DJANGO_ENV")

if DJANGO_ENV:
    # Explicit environment override
    env = DJANGO_ENV
elif os.getenv("K_SERVICE"):
    # Running on Cloud Run without explicit DJANGO_ENV
    # Default to production (should be overridden in terraform for dev/staging)
    env = "production"
else:
    # Local development on laptop/workstation
    env = "local"

print(f"[Django] Loading settings for environment: {env}")

# Import the appropriate settings
if env == "production":
    from .production import *
elif env == "staging":
    from .staging import *
elif env == "development":
    from .development import *
elif env == "local":
    from .local import *
else:
    # Unknown environment - default to local
    print(f"⚠️  WARNING: Unknown environment '{env}'. Defaulting to 'local' settings.")
    from .local import *
