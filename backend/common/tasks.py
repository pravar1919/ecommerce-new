"""Cross-cutting Celery tasks."""

import json
import urllib.request

import structlog
from celery import shared_task
from django.conf import settings
from django.db import transaction

log = structlog.get_logger(__name__)


@shared_task(autoretry_for=(OSError,), retry_backoff=True, max_retries=5)
def revalidate_frontend(tags: list[str]) -> None:
    """Ask Next.js to drop ISR cache entries for these tags (frontend/src/app/api/revalidate)."""
    url = settings.FRONTEND_REVALIDATE_URL
    if not url or not settings.REVALIDATE_SECRET:
        return
    req = urllib.request.Request(  # noqa: S310  (URL comes from settings, not user input)
        url,
        data=json.dumps({"tags": tags}).encode(),
        headers={"Content-Type": "application/json", "X-Revalidate-Secret": settings.REVALIDATE_SECRET},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
        log.info("frontend_revalidated", tags=tags, status=resp.status)


def request_revalidation(*tags: str) -> None:
    """Queue a revalidation after the current transaction commits."""
    if tags:
        transaction.on_commit(lambda: revalidate_frontend.delay(list(tags)))
