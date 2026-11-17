import re
import time
import uuid
from contextvars import ContextVar

import structlog

_request_id: ContextVar[str] = ContextVar("request_id", default="")
_VALID = re.compile(r"^[A-Za-z0-9\-_.]{8,128}$")
log = structlog.get_logger("http")


def get_request_id() -> str:
    return _request_id.get()


class RequestIdMiddleware:
    """Propagates X-Request-ID (set by Caddy) or generates one; binds it to every log line."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get("X-Request-ID", "")
        rid = incoming if _VALID.match(incoming) else uuid.uuid4().hex
        token = _request_id.set(rid)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=rid)
        start = time.perf_counter()
        try:
            response = self.get_response(request)
        finally:
            _request_id.reset(token)
        response["X-Request-ID"] = rid
        user = getattr(request, "user", None)
        log.info(
            "request",
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - start) * 1000, 1),
            user_id=str(user.pk) if user is not None and user.is_authenticated else None,
        )
        return response
