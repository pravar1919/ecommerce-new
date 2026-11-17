from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators
from django.db import models

from common.models import UUIDModel


class TaxClass(UUIDModel):
    name = models.CharField(max_length=80)
    code = models.SlugField(max_length=40, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "tax classes"

    def __str__(self) -> str:
        return self.name


class TaxRule(UUIDModel):
    """GST slab by per-unit transaction value, valid for a date range (no overlaps per class).

    rate applies by comparing the per-unit *transaction value* (after discounts, GST-inclusive
    selling price) with `threshold_paise`. Values must be confirmed by a CA before launch.
    """

    tax_class = models.ForeignKey(TaxClass, on_delete=models.PROTECT, related_name="rules")
    threshold_paise = models.BigIntegerField(help_text="Per-unit value boundary in paise")
    rate_below_bp = models.PositiveIntegerField(help_text="Rate in basis points when value ≤ threshold")
    rate_above_bp = models.PositiveIntegerField(help_text="Rate in basis points when value > threshold")
    effective = DateRangeField(help_text="[from, to) — leave upper bound empty for open-ended")
    notification_ref = models.CharField(max_length=120, blank=True, help_text="Govt. notification reference")

    class Meta:
        ordering = ["tax_class", "-effective"]
        constraints = [
            ExclusionConstraint(
                name="taxrule_no_overlap",
                expressions=[("tax_class", RangeOperators.EQUAL), ("effective", RangeOperators.OVERLAPS)],
            ),
            models.CheckConstraint(
                condition=models.Q(threshold_paise__gt=0), name="taxrule_threshold_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(rate_below_bp__lte=4000, rate_above_bp__lte=4000), name="taxrule_rate_sane"
            ),
        ]

    def __str__(self) -> str:
        below, above = self.rate_below_bp / 100, self.rate_above_bp / 100
        return f"{self.tax_class}: {below}% / {above}% @ ₹{self.threshold_paise // 100}"
