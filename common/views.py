import json
import os
from datetime import datetime

from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    """Endpoint de health check pour la production."""

    def get(self, request):
        checks = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "esm-api",
        }

        db_ok = True
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as exc:
            db_ok = False
            checks["database"] = {"status": "error", "error": str(exc)}
        else:
            checks["database"] = {"status": "ok"}

        redis_ok = True
        try:
            from django.core.cache import cache
            cache.set("healthcheck", "ok", 5)
            val = cache.get("healthcheck")
            if val != "ok":
                redis_ok = False
        except Exception as exc:
            redis_ok = False
            checks["redis"] = {"status": "error", "error": str(exc)}
        else:
            checks["redis"] = {"status": "ok"}

        firebase_ok = True
        try:
            from django.conf import settings
            firebase_creds = getattr(settings, "FIREBASE_CREDENTIALS", "")
            if not firebase_creds:
                firebase_ok = False
        except Exception:
            firebase_ok = False

        checks["firebase"] = {
            "status": "ok" if firebase_ok else "configured"
        }

        if not all([db_ok, redis_ok]):
            checks["status"] = "degraded"
            return JsonResponse(checks, status=503)

        return JsonResponse(checks, status=200)
