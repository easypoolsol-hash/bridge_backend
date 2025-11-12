"""
Health check endpoints for monitoring system status.
Simplified health monitoring for bridge backend.
"""

import time
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """
    Basic health check endpoint - fast and lightweight.

    Returns system status for load balancers and monitoring systems.
    Checks critical services: Django app and database.
    """
    start_time = time.time()
    checks = {}
    overall_status = "healthy"

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e!s}"
        overall_status = "unhealthy"

    response_time = time.time() - start_time

    response_data = {
        "status": overall_status,
        "timestamp": time.time(),
        "service": "bridge-api",
        "version": "1.0.0",
        "response_time_ms": round(response_time * 1000, 2),
        "checks": checks,
    }

    # Return 503 if unhealthy (important for load balancers)
    status_code = 200 if overall_status == "healthy" else 503

    return JsonResponse(response_data, status=status_code)


@require_GET
def liveness_check(request):
    """
    Cloud Run liveness probe - checks if the application is running.

    This should ALWAYS return 200 if the process is alive and can serve requests.
    Does NOT check external dependencies like database.

    If this fails, the container will be restarted.
    """
    return JsonResponse(
        {
            "status": "alive",
            "timestamp": time.time(),
            "service": "bridge-api",
        },
        status=200,
    )


@require_GET
def readiness_check(request):
    """
    Cloud Run readiness probe - checks if app is ready to serve traffic.

    Checks external dependencies (database) with retry logic.
    """
    start_time = time.time()
    checks = {}
    overall_status = "ready"

    # Check database with retry logic
    db_status = "unknown"
    for attempt in range(3):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = "connected"
            break
        except Exception:
            if attempt == 2:  # Last attempt
                db_status = "unavailable"
                overall_status = "degraded"
            else:
                time.sleep(0.5)  # Brief delay between retries

    checks["database"] = db_status

    response_time = time.time() - start_time

    response_data = {
        "status": overall_status,
        "timestamp": time.time(),
        "service": "bridge-api",
        "response_time_ms": round(response_time * 1000, 2),
        "checks": checks,
    }

    # Always return 200 - we're alive and can recover
    return JsonResponse(response_data, status=200)
