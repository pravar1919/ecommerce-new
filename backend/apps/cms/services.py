"""Content writes: versioned publishing, settings changes, newsletter double opt-in."""

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

from common.exceptions import DomainError, InvalidOperation
from common.tasks import request_revalidation

from .blocks import BlockConfigError, validate_config
from .models import ContentBlock, NewsletterSubscriber, Page, PageVersion

NEWSLETTER_SALT = "cms.newsletter"
NEWSLETTER_TOKEN_MAX_AGE = 60 * 60 * 24 * 7


class InvalidBlockConfig(DomainError):
    code = "validation_error"
    default_message = "A block on this page has an invalid configuration."


class InvalidNewsletterToken(DomainError):
    code = "invalid_token"
    default_message = "This link is invalid or has expired."


# ---------- revalidation tags (mirrored in frontend/src/lib/api/tags.ts) -------------------------------
def page_tag(slug: str) -> str:
    return f"cms:page:{slug}"


SITE_SETTINGS_TAG = "cms:site-settings"
NAVIGATION_TAG = "cms:navigation"


# ---------- pages -------------------------------------------------------------------------------------
@transaction.atomic
def create_draft(page: Page, *, from_version: PageVersion | None = None, note: str = "") -> PageVersion:
    """New draft version, optionally copying another version's blocks (e.g. the published one)."""
    Page.objects.select_for_update().get(pk=page.pk)  # serialises version numbering
    draft = PageVersion.objects.create(page=page, note=note)
    if from_version is not None:
        ContentBlock.objects.bulk_create(
            ContentBlock(
                page_version=draft,
                type=b.type,
                position=b.position,
                config=b.config,
                visible_from=b.visible_from,
                visible_until=b.visible_until,
            )
            for b in from_version.blocks.all()
        )
    return draft


def _validate_blocks(version: PageVersion) -> None:
    errors = {}
    for b in version.blocks.all():
        try:
            b.config = validate_config(b.type, b.config)
            b.save(update_fields=["config", "updated_at"])
        except BlockConfigError as exc:
            errors[f"{b.type}#{b.position}"] = exc.messages
    if errors:
        raise InvalidBlockConfig(fields=errors)


@transaction.atomic
def publish_version(version: PageVersion, *, actor=None) -> PageVersion:
    """Make `version` the live one. The previously published version is archived (kept for rollback)."""
    Page.objects.select_for_update().get(pk=version.page_id)
    version.refresh_from_db()
    if version.status == PageVersion.Status.PUBLISHED:
        return version
    if version.status == PageVersion.Status.ARCHIVED and actor is None:
        raise InvalidOperation("Archived versions can only be restored by a staff member.")
    _validate_blocks(version)
    PageVersion.objects.filter(page_id=version.page_id, status=PageVersion.Status.PUBLISHED).update(
        status=PageVersion.Status.ARCHIVED, updated_at=timezone.now()
    )
    version.status = PageVersion.Status.PUBLISHED
    version.published_at = timezone.now()
    version.published_by = actor
    version.save(update_fields=["status", "published_at", "published_by", "updated_at"])
    request_revalidation(page_tag(version.page.slug))
    return version


@transaction.atomic
def schedule_version(version: PageVersion, *, publish_at) -> PageVersion:
    if version.status not in (PageVersion.Status.DRAFT, PageVersion.Status.SCHEDULED):
        raise InvalidOperation("Only drafts can be scheduled.")
    if publish_at <= timezone.now():
        raise InvalidOperation(
            "Choose a time in the future.", fields={"publish_at": ["Must be in the future."]}
        )
    _validate_blocks(version)
    version.status, version.publish_at = PageVersion.Status.SCHEDULED, publish_at
    version.save(update_fields=["status", "publish_at", "updated_at"])
    return version


def publish_due_versions(*, now=None) -> int:
    """Promote scheduled versions whose time has come. For a page with several due, the latest wins."""
    now = now or timezone.now()
    due = PageVersion.objects.filter(status=PageVersion.Status.SCHEDULED, publish_at__lte=now).order_by(
        "page_id", "-publish_at"
    )
    done, seen = 0, set()
    for v in due:
        if v.page_id in seen:
            PageVersion.objects.filter(pk=v.pk).update(status=PageVersion.Status.ARCHIVED, updated_at=now)
            continue
        seen.add(v.page_id)
        try:
            publish_version(v, actor=v.published_by)
            done += 1
        except InvalidBlockConfig:
            PageVersion.objects.filter(pk=v.pk).update(status=PageVersion.Status.DRAFT, updated_at=now)
    return done


def site_settings_changed() -> None:
    request_revalidation(SITE_SETTINGS_TAG)


def navigation_changed() -> None:
    request_revalidation(NAVIGATION_TAG)


# ---------- newsletter (double opt-in) ------------------------------------------------------------------
def _token(sub: NewsletterSubscriber, action: str) -> str:
    return signing.dumps({"id": str(sub.id), "a": action}, salt=NEWSLETTER_SALT, compress=True)


def _read_token(token: str, action: str) -> NewsletterSubscriber:
    try:
        data = signing.loads(token, salt=NEWSLETTER_SALT, max_age=NEWSLETTER_TOKEN_MAX_AGE)
    except signing.BadSignature as exc:
        raise InvalidNewsletterToken() from exc
    if data.get("a") != action:
        raise InvalidNewsletterToken()
    sub = NewsletterSubscriber.objects.filter(pk=data.get("id")).first()
    if sub is None:
        raise InvalidNewsletterToken()
    return sub


@transaction.atomic
def subscribe(*, email: str, source: str = "") -> None:
    """Always 'succeeds' to the caller (no enumeration). Sends a confirmation unless already confirmed."""
    email = email.strip().lower()
    sub, created = NewsletterSubscriber.objects.select_for_update().get_or_create(
        email=email, defaults={"source": source[:40], "consented_at": timezone.now()}
    )
    if not created and sub.status == NewsletterSubscriber.Status.CONFIRMED:
        return
    if not created:
        sub.status, sub.consented_at, sub.unsubscribed_at = (
            NewsletterSubscriber.Status.PENDING,
            timezone.now(),
            None,
        )
        sub.save(update_fields=["status", "consented_at", "unsubscribed_at", "updated_at"])
    link = f"{settings.NEWSLETTER_CONFIRM_URL}?token={_token(sub, 'confirm')}"
    from .tasks import send_newsletter_confirmation

    transaction.on_commit(lambda: send_newsletter_confirmation.delay(sub.email, link))


@transaction.atomic
def confirm_subscription(*, token: str) -> NewsletterSubscriber:
    sub = _read_token(token, "confirm")
    if sub.status != NewsletterSubscriber.Status.CONFIRMED:
        sub.status, sub.confirmed_at = NewsletterSubscriber.Status.CONFIRMED, timezone.now()
        sub.save(update_fields=["status", "confirmed_at", "updated_at"])
    return sub


def unsubscribe_token(sub: NewsletterSubscriber) -> str:
    return _token(sub, "unsubscribe")


@transaction.atomic
def unsubscribe(*, token: str) -> NewsletterSubscriber:
    sub = _read_token(token, "unsubscribe")
    if sub.status != NewsletterSubscriber.Status.UNSUBSCRIBED:
        sub.status, sub.unsubscribed_at = NewsletterSubscriber.Status.UNSUBSCRIBED, timezone.now()
        sub.save(update_fields=["status", "unsubscribed_at", "updated_at"])
    return sub
