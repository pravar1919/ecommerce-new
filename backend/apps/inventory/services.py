"""Stock operations. Every mutation runs in a transaction with row locks taken in a
deterministic order (by StockLevel id) so concurrent checkouts cannot deadlock or oversell."""

from dataclasses import dataclass
from datetime import timedelta

import structlog
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from common.exceptions import InvalidOperation, OutOfStock

from .models import LowStockAlert, StockLevel, StockLocation, StockMovement, StockReservation

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ReservationRequest:
    variant_id: object
    quantity: int


def default_location() -> StockLocation:
    loc = StockLocation.objects.filter(is_default=True, is_active=True).first()
    if loc is None:
        raise InvalidOperation("No default stock location configured.")
    return loc


def _record(
    level: StockLevel, delta: int, reason: str, *, actor=None, note="", ref_type="", ref_id=""
) -> StockMovement:
    return StockMovement.objects.create(
        stock_level=level,
        delta=delta,
        reason=reason,
        balance_after=level.on_hand,
        actor=actor,
        note=note,
        reference_type=ref_type,
        reference_id=str(ref_id) if ref_id else "",
    )


def _check_low_stock(level: StockLevel) -> None:
    if level.available <= level.low_stock_threshold:
        alert, created = LowStockAlert.objects.get_or_create(
            stock_level=level, resolved_at=None, defaults={"available_at_trigger": level.available}
        )
        if created:
            from .tasks import notify_low_stock

            transaction.on_commit(lambda: notify_low_stock.delay(str(alert.pk)))
    else:
        LowStockAlert.objects.filter(stock_level=level, resolved_at=None).update(resolved_at=timezone.now())


@transaction.atomic
def adjust_stock(
    *,
    variant_id,
    delta: int,
    reason: str,
    location: StockLocation | None = None,
    actor=None,
    note: str = "",
    reference_type: str = "",
    reference_id="",
) -> StockLevel:
    if delta == 0:
        raise InvalidOperation("Adjustment must be non-zero.")
    location = location or default_location()
    level, _ = StockLevel.objects.get_or_create(variant_id=variant_id, location=location)
    level = StockLevel.objects.select_for_update().get(pk=level.pk)
    if level.on_hand + delta < level.reserved:
        raise OutOfStock(
            "Cannot reduce stock below the quantity reserved by open checkouts.",
            on_hand=level.on_hand,
            reserved=level.reserved,
        )
    level.on_hand += delta
    level.save(update_fields=["on_hand", "updated_at"])
    _record(level, delta, reason, actor=actor, note=note, ref_type=reference_type, ref_id=reference_id)
    _check_low_stock(level)
    log.info("stock_adjusted", variant_id=str(variant_id), delta=delta, reason=reason, on_hand=level.on_hand)
    return level


@transaction.atomic
def reserve_stock(
    requests: list[ReservationRequest], *, owner_type: str, owner_id, ttl_minutes: int | None = None
) -> list[StockReservation]:
    """Reserve all lines or none. Raises OutOfStock with per-variant availability."""
    ttl = ttl_minutes or settings.CHECKOUT_RESERVATION_TTL_MINUTES
    location = default_location()
    wanted: dict = {}
    for r in requests:
        if r.quantity <= 0:
            raise InvalidOperation("Quantity must be positive.")
        wanted[r.variant_id] = wanted.get(r.variant_id, 0) + r.quantity
    for vid in wanted:
        StockLevel.objects.get_or_create(variant_id=vid, location=location)
    levels = list(
        StockLevel.objects.select_for_update().filter(variant_id__in=wanted, location=location).order_by("pk")
    )
    shortfalls = [
        {"variant_id": str(lv.variant_id), "requested": wanted[lv.variant_id], "available": lv.available}
        for lv in levels
        if lv.available < wanted[lv.variant_id]
    ]
    if shortfalls:
        raise OutOfStock("Some items are no longer available in the requested quantity.", lines=shortfalls)
    expires = timezone.now() + timedelta(minutes=ttl)
    out = []
    for lv in levels:
        lv.reserved += wanted[lv.variant_id]
        lv.save(update_fields=["reserved", "updated_at"])
        out.append(
            StockReservation.objects.create(
                stock_level=lv,
                quantity=wanted[lv.variant_id],
                owner_type=owner_type,
                owner_id=str(owner_id),
                expires_at=expires,
            )
        )
    return out


def _locked_active(reservation_ids) -> list[StockReservation]:
    return list(
        StockReservation.objects.select_for_update()
        .filter(pk__in=reservation_ids, status=StockReservation.Status.ACTIVE)
        .select_related("stock_level")
        .order_by("stock_level_id")
    )


@transaction.atomic
def release_reservations(reservation_ids, *, status: str = StockReservation.Status.RELEASED) -> int:
    """Idempotent: already released/committed reservations are skipped."""
    reservations = _locked_active(reservation_ids)
    levels = {
        lv.pk: lv
        for lv in StockLevel.objects.select_for_update()
        .filter(pk__in={r.stock_level_id for r in reservations})
        .order_by("pk")
    }
    for r in reservations:
        lv = levels[r.stock_level_id]
        lv.reserved -= r.quantity
        lv.save(update_fields=["reserved", "updated_at"])
        r.status = status
        r.save(update_fields=["status", "updated_at"])
    return len(reservations)


@transaction.atomic
def commit_reservations(reservation_ids, *, reference_type: str, reference_id) -> int:
    """Convert reservations into sales: on_hand and reserved both decrease; ledger records the sale."""
    reservations = _locked_active(reservation_ids)
    levels = {
        lv.pk: lv
        for lv in StockLevel.objects.select_for_update()
        .filter(pk__in={r.stock_level_id for r in reservations})
        .order_by("pk")
    }
    for r in reservations:
        lv = levels[r.stock_level_id]
        lv.reserved -= r.quantity
        lv.on_hand -= r.quantity
        lv.save(update_fields=["reserved", "on_hand", "updated_at"])
        _record(lv, -r.quantity, StockMovement.Reason.SALE, ref_type=reference_type, ref_id=reference_id)
        r.status = StockReservation.Status.COMMITTED
        r.save(update_fields=["status", "updated_at"])
        _check_low_stock(lv)
    return len(reservations)


def extend_reservations(reservation_ids, *, ttl_minutes: int | None = None) -> int:
    ttl = ttl_minutes or settings.CHECKOUT_RESERVATION_TTL_MINUTES
    return StockReservation.objects.filter(
        pk__in=reservation_ids, status=StockReservation.Status.ACTIVE
    ).update(expires_at=timezone.now() + timedelta(minutes=ttl))


def release_expired_reservations(batch_size: int = 500) -> int:
    ids = list(
        StockReservation.objects.filter(
            status=StockReservation.Status.ACTIVE, expires_at__lte=timezone.now()
        ).values_list("pk", flat=True)[:batch_size]
    )
    return release_reservations(ids, status=StockReservation.Status.EXPIRED) if ids else 0
