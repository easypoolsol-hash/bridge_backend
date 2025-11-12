# Multi-stage optimized Dockerfile for Bridge Backend
# Optimized for frequent rebuilds with maximum layer caching

# =============================================================================
# Stage 1: Build dependencies (cached when pyproject.toml doesn't change)
# =============================================================================
FROM python:3.11-slim-bookworm AS builder

# Set environment variables for better caching and performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system build dependencies (minimal set for Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip first (cached layer)
RUN pip install --upgrade pip setuptools wheel

# Copy dependency files first (for better caching)
# This layer only changes when dependencies change
COPY pyproject.toml ./

# Parse pyproject.toml and install dependencies
RUN python -c "import tomllib; import subprocess; import sys; data = tomllib.load(open('pyproject.toml', 'rb')); deps = data.get('project', {}).get('dependencies', []); subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir'] + deps, check=True) if deps else None"

# Install production runtime dependencies
RUN pip install gunicorn>=22.0.0 whitenoise>=6.6.0

# =============================================================================
# Stage 2: Runtime image (minimal and secure)
# =============================================================================
FROM python:3.11-slim-bookworm AS runtime

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && groupadd -r django && useradd -r -g django django

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code (changes frequently, so placed after dependencies)
COPY --chown=django:django app/ .

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app

# Collect static files (safe to do at build time)
RUN python manage.py collectstatic --noinput --clear

# DO NOT run migrations at build time - they should run at deployment time

# Switch to non-root user for security
USER django

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Create production-grade startup script
USER root
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Starting Bridge Backend"\n\
\n\
# Function to run database operations in background\n\
run_db_init() {\n\
    echo "📦 [BACKGROUND] Starting database initialization..."\n\
    \n\
    # Wait for database with exponential backoff\n\
    attempt=1\n\
    max_attempts=12\n\
    wait_time=5\n\
    \n\
    while [ $attempt -le $max_attempts ]; do\n\
        echo "⏳ [DB-INIT] Attempt $attempt/$max_attempts: Checking database..."\n\
        if python manage.py check --database default 2>/dev/null; then\n\
            echo "✅ [DB-INIT] Database connected on attempt $attempt"\n\
            break\n\
        fi\n\
        \n\
        if [ $attempt -eq $max_attempts ]; then\n\
            echo "⚠️  [DB-INIT] Database failed after $max_attempts attempts"\n\
            return 1\n\
        fi\n\
        \n\
        sleep $wait_time\n\
        wait_time=$((wait_time + 5))\n\
        if [ $wait_time -gt 30 ]; then\n\
            wait_time=30\n\
        fi\n\
        attempt=$((attempt + 1))\n\
    done\n\
    \n\
    # Run migrations\n\
    echo "📦 [DB-INIT] Running migrations..."\n\
    if python manage.py migrate --noinput; then\n\
        echo "✅ [DB-INIT] Migrations completed"\n\
    else\n\
        echo "⚠️  [DB-INIT] Migrations failed"\n\
        return 1\n\
    fi\n\
}\n\
\n\
# Start database initialization in background\n\
run_db_init &\n\
\n\
# Give database init a brief head start\n\
sleep 2\n\
\n\
# Start the server IMMEDIATELY\n\
echo "✅ Application starting on port 8000"\n\
echo "🔐 Admin: /admin/ (admin / admin)"\n\
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 0 bridge_backend.wsgi:application' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown django:django /app/start.sh

USER django

# Use the startup script
CMD ["/app/start.sh"]
