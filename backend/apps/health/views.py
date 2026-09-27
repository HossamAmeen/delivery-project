"""``/api/status/`` (public), ``/api/health/`` and ``/api/health/ready/`` (token)."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.openapi import ErrorEnvelopeSerializer
from common.throttling import HealthRateThrottle

from . import services
from .serializers import HealthSerializer, ReadinessSerializer, StatusSerializer

TOKEN_PARAMETERS = [
    OpenApiParameter(
        name=services.HEALTH_TOKEN_HEADER,
        location=OpenApiParameter.HEADER,
        required=False,
        description="Health check token (preferred).",
    ),
    OpenApiParameter(
        name=services.HEALTH_TOKEN_QUERY_PARAM,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Health check token (DRF_SKILL compatibility; tooling uses the header).",
    ),
]
INVALID_TOKEN_RESPONSE = OpenApiResponse(
    ErrorEnvelopeSerializer,
    description="Missing or wrong token: `Invalid health check password.` "
    "(`errors.code` = `HEALTH_TOKEN_INVALID`).",
)


class _HealthBaseView(APIView):
    # No JWT: a stale browser token must never break these endpoints.
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [HealthRateThrottle]


class StatusView(_HealthBaseView):
    """Public, browser-safe liveness (ADR-019). Reveals nothing but "ok"."""

    @extend_schema(
        tags=["health"],
        summary="Public API status",
        responses={200: StatusSerializer},
        auth=[],
    )
    def get(self, request):
        return Response({"status": "ok"})


class HealthView(_HealthBaseView):
    """The Django application is running (no dependency checks)."""

    @extend_schema(
        tags=["health"],
        summary="Health check (token)",
        parameters=TOKEN_PARAMETERS,
        responses={200: HealthSerializer, 401: INVALID_TOKEN_RESPONSE},
        auth=[],
    )
    def get(self, request):
        services.verify_health_token(request)
        return Response({"status": "healthy"}, headers={"Cache-Control": "no-store"})


class ReadinessView(_HealthBaseView):
    """Database, cache and (when enabled) Celery broker."""

    @extend_schema(
        tags=["health"],
        summary="Readiness check (token)",
        parameters=TOKEN_PARAMETERS,
        responses={
            200: ReadinessSerializer,
            401: INVALID_TOKEN_RESPONSE,
            503: OpenApiResponse(
                ErrorEnvelopeSerializer,
                description="`Service not ready.`; `errors.checks` names each check "
                "(`ok`/`error`/`skipped`), `errors.code` = `SERVICE_NOT_READY`.",
            ),
        },
        auth=[],
    )
    def get(self, request):
        services.verify_health_token(request)
        checks = services.run_readiness_checks()
        if not services.is_ready(checks):
            raise services.ServiceNotReady(extra={"checks": checks})
        return Response(
            {"status": "ready", "checks": checks}, headers={"Cache-Control": "no-store"}
        )
