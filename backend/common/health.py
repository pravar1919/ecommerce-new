from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

_HealthSerializer = inline_serializer(
    "Health",
    {"status": serializers.CharField(), "checks": serializers.DictField(child=serializers.CharField())},
)


class LivenessView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=_HealthSerializer, tags=["health"])
    def get(self, request):
        return Response({"status": "ok", "checks": {}})


class HealthView(APIView):
    """Readiness: verifies the database and cache. Returns 503 if any dependency fails."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=_HealthSerializer, tags=["health"])
    def get(self, request):
        checks: dict[str, str] = {}
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"
        try:
            cache.set("health:ping", "1", 5)
            checks["cache"] = "ok" if cache.get("health:ping") == "1" else "error"
        except Exception:
            checks["cache"] = "error"
        healthy = all(v == "ok" for v in checks.values())
        return Response(
            {"status": "ok" if healthy else "degraded", "checks": checks}, status=200 if healthy else 503
        )
