from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from . import selectors, services


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_newsletter_confirmation(email: str, link: str) -> None:
    # Templated notifications arrive with the notifications app (Phase 7).
    brand = selectors.site_settings().brand_name
    send_mail(
        subject=f"Confirm your subscription to {brand}",
        message=f"Please confirm you'd like to hear from {brand}:\n\n{link}\n\n"
        "If you didn't sign up, ignore this email and you won't hear from us.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )


@shared_task
def publish_due_versions() -> int:
    return services.publish_due_versions()
