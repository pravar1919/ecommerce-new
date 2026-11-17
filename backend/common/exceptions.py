"""Domain errors and the API error envelope (see docs/api-contracts.md)."""

from typing import Any

import structlog
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exc
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .middleware import get_request_id

log = structlog.get_logger(__name__)


class DomainError(Exception):
    """Base class for business-rule violations raised by services."""

    code = "domain_error"
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "The request could not be completed."

    def __init__(self, message: str | None = None, *, fields: dict | None = None, **details: Any) -> None:
        self.message = message or self.default_message
        self.fields = fields
        self.details = details
        super().__init__(self.message)


class NotFound(DomainError):
    code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Not found."


class Conflict(DomainError):
    code = "conflict"
    status_code = status.HTTP_409_CONFLICT
    default_message = "Conflict."


class OutOfStock(Conflict):
    code = "out_of_stock"
    default_message = "Not enough stock."


class InvalidOperation(DomainError):
    code = "invalid_operation"


_DRF_CODES = {
    drf_exc.ValidationError: "validation_error",
    drf_exc.ParseError: "validation_error",
    drf_exc.NotAuthenticated: "not_authenticated",
    drf_exc.AuthenticationFailed: "not_authenticated",
    drf_exc.PermissionDenied: "permission_denied",
    drf_exc.NotFound: "not_found",
    drf_exc.MethodNotAllowed: "method_not_allowed",
    drf_exc.Throttled: "rate_limited",
    drf_exc.UnsupportedMediaType: "unsupported_media_type",
}


def _envelope(code: str, message: str, *, details=None, fields=None) -> dict:
    body: dict[str, Any] = {"code": code, "message": message, "request_id": get_request_id()}
    if details:
        body["details"] = details
    if fields:
        body["fields"] = fields
    return {"error": body}


def api_exception_handler(exc: Exception, context: dict) -> Response | None:
    if isinstance(exc, DomainError):
        return Response(
            _envelope(exc.code, exc.message, details=exc.details, fields=exc.fields), status=exc.status_code
        )

    if isinstance(exc, Http404):
        exc = drf_exc.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = drf_exc.PermissionDenied()

    response = exception_handler(exc, context)
    if response is None:
        return None  # unhandled -> 500 via Django, logged by middleware

    code = next((c for cls, c in _DRF_CODES.items() if isinstance(exc, cls)), "error")
    if isinstance(exc, drf_exc.ValidationError):
        data = exc.detail
        if isinstance(data, dict):
            non_field = data.pop("non_field_errors", None) if isinstance(data, dict) else None
            message = str(non_field[0]) if non_field else "Please correct the highlighted fields."
            response.data = _envelope(code, message, fields=data or None)
        else:
            items = data if isinstance(data, list) else [data]
            response.data = _envelope(code, str(items[0]) if items else "Invalid request.")
    else:
        detail = getattr(exc, "detail", "")
        response.data = _envelope(code, str(detail))
    return response
