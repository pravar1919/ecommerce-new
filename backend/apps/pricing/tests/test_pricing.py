import datetime as dt
import random

import pytest
from django.contrib.postgres.fields.ranges import DateRange
from django.db import IntegrityError

from apps.pricing.models import TaxRule
from apps.pricing.services import TaxRuleMissing, allocate_discount, gst_rate_bp, split_inclusive

# Golden cases: (gross paise, rate bp, intra_state) -> (taxable, cgst, sgst, igst)
GOLDEN = [
    (105_000, 500, True, (100_000, 2_500, 2_500, 0)),  # ₹1,050 @5% intra
    (105_000, 500, False, (100_000, 0, 0, 5_000)),  # inter-state -> IGST
    (11_800_00, 1800, True, (10_000_00, 90_000, 90_000, 0)),
    (12_450_000, 1800, False, (10_550_847, 0, 0, 1_899_153)),
    (99, 500, True, (94, 3, 2, 0)),  # odd paisa goes to CGST
    (0, 1800, True, (0, 0, 0, 0)),
]


@pytest.mark.parametrize("gross,rate,intra,expected", GOLDEN)
def test_split_inclusive_golden(gross, rate, intra, expected):
    b = split_inclusive(gross, rate, intra_state=intra)
    assert (b.taxable_paise, b.cgst_paise, b.sgst_paise, b.igst_paise) == expected
    assert b.taxable_paise + b.tax_paise == gross


def test_split_inclusive_always_reconciles():
    rng = random.Random(7)
    for _ in range(2000):
        gross, rate = rng.randint(0, 50_000_000), rng.choice([0, 500, 1200, 1800, 2800])
        b = split_inclusive(gross, rate, intra_state=rng.random() < 0.5)
        assert b.taxable_paise + b.tax_paise == gross
        assert abs(b.cgst_paise - b.sgst_paise) <= 1


def test_allocate_discount_exact_and_bounded():
    assert allocate_discount([10_000, 20_000, 30_000], 6_000) == [1_000, 2_000, 3_000]
    assert sum(allocate_discount([333, 333, 334], 100)) == 100
    assert allocate_discount([500, 500], 5_000) == [500, 500]  # capped at total
    assert allocate_discount([], 100) == [] and allocate_discount([0, 0], 10) == [0, 0]
    rng = random.Random(3)
    for _ in range(1000):
        lines = [rng.randint(1, 2_000_000) for _ in range(rng.randint(1, 8))]
        d = rng.randint(0, sum(lines))
        shares = allocate_discount(lines, d)
        assert sum(shares) == d and all(0 <= s <= lt for s, lt in zip(shares, lines, strict=True))


@pytest.mark.django_db
def test_gst_rate_by_threshold_and_date(tax_class):
    on = dt.date(2026, 1, 1)
    assert gst_rate_bp(tax_class.pk, 250_000, on) == 500  # exactly ₹2,500 -> lower slab
    assert gst_rate_bp(tax_class.pk, 250_001, on) == 1800
    with pytest.raises(TaxRuleMissing):
        gst_rate_bp(tax_class.pk, 100_000, dt.date(2025, 1, 1))  # before rule's effective date


@pytest.mark.django_db
def test_overlapping_tax_rules_rejected_by_db(tax_class):
    with pytest.raises(IntegrityError):
        TaxRule.objects.create(
            tax_class=tax_class,
            threshold_paise=100_000,
            rate_below_bp=500,
            rate_above_bp=1200,
            effective=DateRange(dt.date(2026, 4, 1), dt.date(2027, 4, 1)),
        )
