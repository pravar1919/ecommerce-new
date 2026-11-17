import threading
from datetime import timedelta

import pytest
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from apps.inventory import services
from apps.inventory.models import LowStockAlert, StockLevel, StockMovement, StockReservation
from apps.inventory.services import ReservationRequest
from common.exceptions import InvalidOperation, OutOfStock


@pytest.fixture
def variants(catalog):
    p = catalog.product("Stocked", colours=("Ivory",), sizes=("38", "40"), stock=0)
    return list(p.variants.order_by("sku"))


def level(v):
    return StockLevel.objects.get(variant=v)


@pytest.mark.django_db
def test_adjust_writes_ledger_and_balance(variants):
    v = variants[0]
    services.adjust_stock(variant_id=v.pk, delta=10, reason="receipt")
    services.adjust_stock(variant_id=v.pk, delta=-3, reason="damage", note="torn")
    assert level(v).on_hand == 7
    moves = list(StockMovement.objects.filter(stock_level__variant=v).order_by("created_at"))
    assert [(m.delta, m.balance_after) for m in moves] == [(10, 10), (-3, 7)]
    with pytest.raises(InvalidOperation):
        services.adjust_stock(variant_id=v.pk, delta=0, reason="adjustment")
    with pytest.raises(OutOfStock):
        services.adjust_stock(variant_id=v.pk, delta=-8, reason="adjustment")


@pytest.mark.django_db
def test_ledger_is_append_only(variants):
    services.adjust_stock(variant_id=variants[0].pk, delta=5, reason="receipt")
    m = StockMovement.objects.get()
    with pytest.raises(RuntimeError):
        m.save()
    with pytest.raises(RuntimeError):
        m.delete()


@pytest.mark.django_db
def test_reserve_all_or_nothing(variants):
    a, b = variants
    services.adjust_stock(variant_id=a.pk, delta=5, reason="receipt")
    services.adjust_stock(variant_id=b.pk, delta=1, reason="receipt")
    with pytest.raises(OutOfStock) as exc:
        services.reserve_stock(
            [ReservationRequest(a.pk, 2), ReservationRequest(b.pk, 2)],
            owner_type="checkout_session",
            owner_id="cs1",
        )
    assert exc.value.details["lines"] == [{"variant_id": str(b.pk), "requested": 2, "available": 1}]
    assert level(a).reserved == 0 and StockReservation.objects.count() == 0

    res = services.reserve_stock(
        [ReservationRequest(a.pk, 2), ReservationRequest(a.pk, 1)],
        owner_type="checkout_session",
        owner_id="cs1",
    )
    assert len(res) == 1 and res[0].quantity == 3 and level(a).reserved == 3


@pytest.mark.django_db
def test_cannot_adjust_below_reserved(variants):
    v = variants[0]
    services.adjust_stock(variant_id=v.pk, delta=4, reason="receipt")
    services.reserve_stock([ReservationRequest(v.pk, 3)], owner_type="cs", owner_id="1")
    with pytest.raises(OutOfStock):
        services.adjust_stock(variant_id=v.pk, delta=-2, reason="adjustment")


@pytest.mark.django_db
def test_release_is_idempotent_and_commit_records_sale(variants):
    v = variants[0]
    services.adjust_stock(variant_id=v.pk, delta=5, reason="receipt")
    r1 = services.reserve_stock([ReservationRequest(v.pk, 2)], owner_type="cs", owner_id="1")[0]
    assert services.release_reservations([r1.pk]) == 1
    assert services.release_reservations([r1.pk]) == 0
    assert level(v).reserved == 0

    r2 = services.reserve_stock([ReservationRequest(v.pk, 2)], owner_type="cs", owner_id="2")[0]
    assert services.commit_reservations([r2.pk], reference_type="order", reference_id="AT-1") == 1
    assert services.commit_reservations([r2.pk], reference_type="order", reference_id="AT-1") == 0
    lv = level(v)
    assert (lv.on_hand, lv.reserved) == (3, 0)
    sale = StockMovement.objects.get(reason="sale")
    assert (sale.delta, sale.reference_id) == (-2, "AT-1")


@pytest.mark.django_db
def test_expired_reservations_released(variants):
    v = variants[0]
    services.adjust_stock(variant_id=v.pk, delta=2, reason="receipt")
    r = services.reserve_stock([ReservationRequest(v.pk, 2)], owner_type="cs", owner_id="1")[0]
    StockReservation.objects.filter(pk=r.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert services.release_expired_reservations() == 1
    r.refresh_from_db()
    assert r.status == "expired" and level(v).reserved == 0


@pytest.mark.django_db
def test_low_stock_alert_opens_once_and_resolves(variants, django_capture_on_commit_callbacks):
    v = variants[0]
    with django_capture_on_commit_callbacks():
        services.adjust_stock(variant_id=v.pk, delta=1, reason="receipt")  # 1 <= threshold 2
        services.adjust_stock(variant_id=v.pk, delta=1, reason="receipt")  # still low, no duplicate
    assert LowStockAlert.objects.filter(resolved_at=None).count() == 1
    services.adjust_stock(variant_id=v.pk, delta=10, reason="receipt")
    assert LowStockAlert.objects.filter(resolved_at=None).count() == 0


@pytest.mark.django_db
def test_db_rejects_reserved_above_on_hand(variants):
    services.adjust_stock(variant_id=variants[0].pk, delta=1, reason="receipt")
    with pytest.raises(IntegrityError), transaction.atomic():
        StockLevel.objects.filter(variant=variants[0]).update(reserved=2)


@pytest.mark.django_db(transaction=True)
def test_concurrent_checkouts_cannot_oversell_last_unit(variants):
    v = variants[0]
    services.adjust_stock(variant_id=v.pk, delta=1, reason="receipt")
    barrier = threading.Barrier(5)
    results: list[str] = []

    def buyer(i):
        try:
            barrier.wait()
            services.reserve_stock([ReservationRequest(v.pk, 1)], owner_type="cs", owner_id=f"buyer-{i}")
            results.append("ok")
        except OutOfStock:
            results.append("out")
        finally:
            connection.close()

    threads = [threading.Thread(target=buyer, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["ok", "out", "out", "out", "out"]
    lv = level(v)
    assert (lv.on_hand, lv.reserved) == (1, 1)
