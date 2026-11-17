from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_password_reset_email(email: str, link: str) -> None:
    # Templated notifications arrive with the notifications app (Phase 7).
    send_mail(
        subject=f"Reset your {settings.BRAND_NAME} password",
        message=f"Use this link to choose a new password (valid for 3 days):\n\n{link}\n\n"
        "If you didn't request this, you can ignore this email.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
