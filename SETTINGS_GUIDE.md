# Django Settings Guide

## Environment-Based Configuration

Following Fortune 500 / Google Cloud best practices, settings are organized by environment with automatic detection.

## Settings Structure

```
bridge_backend/settings/
├── __init__.py       # Auto-detects environment and imports appropriate settings
├── base.py           # Shared configuration across all environments
├── development.py    # Local development settings
├── staging.py        # Staging environment settings
├── production.py     # Production environment settings (Cloud Run)
```

## Auto-Detection Logic

The system automatically detects the environment in this order:

1. **DJANGO_ENV** environment variable (explicit override)
2. **K_SERVICE** environment variable (Cloud Run detection → production)
3. **Default**: development

```python
# Examples:
DJANGO_ENV=development  # Force development
DJANGO_ENV=staging      # Force staging
# On Cloud Run: K_SERVICE exists → automatically uses production
# Locally: No env vars → automatically uses development
```

## Environment Configurations

### Development (Local)

**Auto-activates when**: No environment variables set

**Features**:
- ✅ SQLite database (no PostgreSQL needed)
- ✅ DEBUG = True
- ✅ CORS allow all origins (no CORS errors)
- ✅ Secret key hardcoded (no .env needed)
- ✅ Firebase optional (can test without Firebase)
- ✅ Verbose logging

**Database**: `db.sqlite3` (auto-created)

**How to use**:
```bash
# Just run - no setup needed!
python manage.py migrate
python manage.py runserver
```

### Staging

**Auto-activates when**: `DJANGO_ENV=staging`

**Features**:
- ✅ PostgreSQL (Cloud SQL)
- ✅ Production-like security
- ✅ Relaxed CORS for testing (includes localhost)
- ⚠️ Requires environment variables
- 🔐 Firebase required

**Required Environment Variables**:
```bash
DJANGO_ENV=staging
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ALLOWED_HOSTS=your-staging-url.run.app
CORS_ALLOWED_ORIGINS=https://your-frontend.com
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

**CORS**: Allows configured origins + localhost (8080-8084) for testing

### Production (Cloud Run)

**Auto-activates when**: `K_SERVICE` environment variable exists (Cloud Run)

**Features**:
- 🔒 Maximum security
- 🔒 DEBUG = False
- 🔒 Strict CORS (only configured origins)
- 🔒 HTTPS enforcement
- 🔒 Secure cookies
- 🔐 Firebase required
- 📊 Structured JSON logging

**Required Environment Variables**:
```bash
# Auto-set by Cloud Run:
K_SERVICE=bridge-api-dev

# Required from Secret Manager/Terraform:
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ALLOWED_HOSTS=bridge-api-dev-123.asia-south1.run.app
CORS_ALLOWED_ORIGINS=https://your-production-frontend.com
CSRF_TRUSTED_ORIGINS=https://bridge-api-dev-123.asia-south1.run.app
FIREBASE_CREDENTIALS_PATH=/secrets/firebase-credentials.json
```

## Quick Start

### Local Development

```bash
# No setup needed - just run!
cd backend_bridge/app
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_insurance_categories
python manage.py runserver

# You'll see:
# 🔧 Loading settings for environment: development
# ⚠️  Warning: FIREBASE_CREDENTIALS_PATH not set. Firebase authentication disabled for development.
```

### Testing Staging Locally

```bash
# Set staging environment
export DJANGO_ENV=staging
export SECRET_KEY=test-key
export DATABASE_URL=postgresql://user:pass@localhost:5432/bridge_staging
export ALLOWED_HOSTS=localhost,127.0.0.1
export CORS_ALLOWED_ORIGINS=http://localhost:8080
export FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json

python manage.py runserver

# You'll see:
# 🔧 Loading settings for environment: staging
```

### Cloud Run Deployment

```bash
# No DJANGO_ENV needed - auto-detects Cloud Run!
# Just ensure environment variables are set via Terraform/Secret Manager

gcloud run deploy bridge-api-dev \
  --set-env-vars SECRET_KEY=xxx \
  --set-env-vars DATABASE_URL=xxx \
  --set-env-vars ALLOWED_HOSTS=xxx \
  ...

# App will see K_SERVICE and automatically use production settings
# Logs will show:
# 🔧 Loading settings for environment: production
```

## Benefits

### ✅ No More If/Else Chains

**Before**:
```python
if DEBUG:
    CORS_ALLOW_ALL = True
else:
    if os.getenv("STAGING"):
        CORS_ALLOWED_ORIGINS = [...]
    else:
        CORS_ALLOWED_ORIGINS = [...]
```

**After**:
```python
# Each environment file is clean and focused
# development.py
CORS_ALLOW_ALL_ORIGINS = True

# production.py
CORS_ALLOWED_ORIGINS = [...]
```

### ✅ Clear Separation of Concerns

- **base.py**: Django apps, middleware, REST Framework config (never changes)
- **development.py**: SQLite, relaxed security (for fast local dev)
- **staging.py**: PostgreSQL, production-like (for testing)
- **production.py**: Maximum security (for Cloud Run)

### ✅ Auto-Detection

- **Local dev**: Just works, no setup
- **Cloud Run**: Detects `K_SERVICE`, uses production
- **Explicit override**: `DJANGO_ENV` for testing

### ✅ Environment-Specific Behavior

| Feature | Development | Staging | Production |
|---------|------------|---------|------------|
| Database | SQLite | PostgreSQL | PostgreSQL |
| DEBUG | True | False | False |
| CORS | Allow all | Configured + localhost | Strict |
| Firebase | Optional | Required | Required |
| Logging | Verbose | JSON | JSON |
| HTTPS | No | Yes | Yes |

## Troubleshooting

### Error: "SECRET_KEY environment variable is required"

**Solution**: You're in staging/production but SECRET_KEY is not set.

```bash
# For staging:
export SECRET_KEY=your-secret-key

# For production:
# Set via Terraform/Secret Manager
```

### Error: "DATABASE_URL environment variable is required"

**Solution**: You're in staging/production but DATABASE_URL is not set.

```bash
# For staging:
export DATABASE_URL=postgresql://user:pass@localhost:5432/bridge_staging

# For production:
# Set via Terraform/Secret Manager
```

### Django uses wrong environment

**Solution**: Check environment detection:

```bash
# See which environment is detected:
python manage.py shell

# You'll see:
# 🔧 Loading settings for environment: development

# Force specific environment:
export DJANGO_ENV=staging
python manage.py shell

# You'll see:
# 🔧 Loading settings for environment: staging
```

### CORS errors in development

**Solution**: Development should allow all CORS. Check:

```bash
python manage.py shell
>>> from django.conf import settings
>>> print(settings.CORS_ALLOW_ALL_ORIGINS)
# Should print: True

# If False, you're not in development mode:
>>> import os
>>> os.getenv('DJANGO_ENV')
>>> os.getenv('K_SERVICE')
```

## Migration from Old Settings

**Old**: Single `settings.py` with if/else logic

**New**: Environment-based settings with auto-detection

**Changes needed**:
- None! Old settings.py was deleted and replaced with settings/ directory
- Django automatically uses `bridge_backend.settings` (looks in settings/ folder)
- No import changes needed in your code
