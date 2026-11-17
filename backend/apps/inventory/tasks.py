from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from . import services
from .models import LowStockAlert


@shared_task
def release_expired_reservations() -> int:
    return services.release_expired_reservations()


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def notify_low_stock(alert_id: str) -> None:
    alert = LowStockAlert.objects.select_related(
        "stock_level__variant__product", "stock_level__location"
    ).get(pk=alert_id)
    recipients = list(
        get_user_model()
        .objects.filter(is_active=True, is_staff=True, groups__name="Inventory Manager")
        .values_list("email", flat=True)
    )
    if not recipients:
        return
    lv = alert.stock_level
    send_mail(
        subject=f"Low stock: {lv.variant.sku} ({alert.available_at_trigger} left)",
        message=f"{lv.variant.product.name} — {lv.variant.sku} at {lv.location.name} has "
        f"{alert.available_at_trigger} available (threshold {lv.low_stock_threshold}).",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
    )
