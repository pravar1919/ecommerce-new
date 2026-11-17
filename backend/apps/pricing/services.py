"""Pure pricing primitives: GST rate lookup, inclusive-tax split, discount allocation.

All amounts are integer paise; rates are basis points (1800 = 18%).
"""

import datetime as dt
from dataclasses import dataclass

from django.utils import timezone

from common.exceptions import DomainError

from .models import TaxRule

BP = 10_000


class TaxRuleMissing(DomainError):
    code = "tax_rule_missing"
    status_code = 500
    default_message = "No tax rule is configured for this product."


@dataclass(frozen=True, slots=True)
class TaxBreakdown:
    gross_paise: int
    taxable_paise: int
    rate_bp: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int

    @property
    def tax_paise(self) -> int:
        return self.cgst_paise + self.sgst_paise + self.igst_paise


def effective_unit_price(mrp_paise: int, sale_price_paise: int | None) -> int:
    return sale_price_paise if sale_price_paise is not None else mrp_paise


def gst_rate_bp(tax_class_id, unit_value_paise: int, on: dt.date | None = None) -> int:
    on = on or timezone.localdate()
    rule = (
        TaxRule.objects.filter(tax_class_id=tax_class_id, effective__contains=on).only(
            "threshold_paise", "rate_below_bp", "rate_above_bp"
        )
    ).first()
    if rule is None:
        raise TaxRuleMissing(tax_class_id=str(tax_class_id), on=on.isoformat())
    return rule.rate_below_bp if unit_value_paise <= rule.threshold_paise else rule.rate_above_bp


def split_inclusive(gross_paise: int, rate_bp: int, *, intra_state: bool) -> TaxBreakdown:
    """Back-calculate GST from a GST-inclusive amount.

    taxable = round(gross * 10000 / (10000 + rate)); tax = gross - taxable.
    Intra-state: CGST + SGST (odd paisa to CGST). Inter-state: IGST.
    """
    if gross_paise < 0:
        raise ValueError("gross must be non-negative")
    taxable = (gross_paise * BP * 2 + (BP + rate_bp)) // (2 * (BP + rate_bp))  # round half up
    tax = gross_paise - taxable
    if intra_state:
        sgst = tax // 2
        return TaxBreakdown(gross_paise, taxable, rate_bp, tax - sgst, sgst, 0)
    return TaxBreakdown(gross_paise, taxable, rate_bp, 0, 0, tax)


def allocate_discount(line_totals: list[int], discount_paise: int) -> list[int]:
    """Allocate an order-level discount across lines pro rata (largest-remainder method).

    The result sums exactly to `discount_paise` and never exceeds any line total.
    """
    total = sum(line_totals)
    if discount_paise < 0:
        raise ValueError("discount must be non-negative")
    if total == 0 or discount_paise == 0:
        return [0] * len(line_totals)
    discount_paise = min(discount_paise, total)
    raw = [lt * discount_paise for lt in line_totals]
    shares = [r // total for r in raw]
    remainder = discount_paise - sum(shares)
    order = sorted(range(len(line_totals)), key=lambda i: (raw[i] % total, line_totals[i]), reverse=True)
    for i in order[:remainder]:
        shares[i] += 1
    return shares
