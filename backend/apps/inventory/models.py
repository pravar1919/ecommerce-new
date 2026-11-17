from django.conf import settings
from django.db import models

from common.models import UUIDModel


class StockLocation(UUIDModel):
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=30, unique=True)
    address = models.TextField(blank=True)
    state_code = models.CharField(max_length=2, help_text="GST state code of this dispatch location")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"], condition=models.Q(is_default=True), name="one_default_location"
            )
        ]

    def __str__(self) -> str:
        return self.name


class StockLevel(UUIDModel):
    """Current stock of one variant at one location. Mutated only via inventory.services."""

    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="stock_levels"
    )
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name="stock_levels")
    on_hand = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["variant", "location"], name="stocklevel_unique"),
            models.CheckConstraint(condition=models.Q(on_hand__gte=0), name="stocklevel_on_hand_nonneg"),
            models.CheckConstraint(condition=models.Q(reserved__gte=0), name="stocklevel_reserved_nonneg"),
            models.CheckConstraint(
                condition=models.Q(reserved__lte=models.F("on_hand")), name="stocklevel_reserved_le_on_hand"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.variant} @ {self.location}: {self.available} available"

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


class StockReservation(UUIDModel):
    """Holds stock for a checkout. Owner is generic so inventory never depends on checkout/orders."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMMITTED = "committed", "Committed (sold)"
        RELEASED = "released", "Released"
        EXPIRED = "expired", "Expired"

    stock_level = models.ForeignKey(StockLevel, on_delete=models.PROTECT, related_name="reservations")
    quantity = models.PositiveIntegerField()
    owner_type = models.CharField(max_length=40, help_text="e.g. checkout_session")
    owner_id = models.CharField(max_length=64)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["owner_type", "owner_id"]),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="reservation_qty_positive")
        ]


class StockMovement(UUIDModel):
    """Append-only ledger. Corrections are new movements; rows are never updated or deleted."""

    class Reason(models.TextChoices):
        RECEIPT = "receipt", "Goods received"
        SALE = "sale", "Sale"
        CANCELLATION = "cancellation", "Order cancellation restock"
        RETURN = "return", "Customer return restock"
        ADJUSTMENT = "adjustment", "Manual adjustment / stock count"
        DAMAGE = "damage", "Damaged / write-off"
        TRANSFER = "transfer", "Transfer between locations"

    stock_level = models.ForeignKey(StockLevel, on_delete=models.PROTECT, related_name="movements")
    delta = models.IntegerField()
    reason = models.CharField(max_length=14, choices=Reason.choices)
    balance_after = models.IntegerField()
    reference_type = models.CharField(max_length=40, blank=True)
    reference_id = models.CharField(max_length=64, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(delta=0), name="movement_delta_nonzero"),
            models.CheckConstraint(condition=models.Q(balance_after__gte=0), name="movement_balance_nonneg"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise RuntimeError("StockMovement is append-only")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("StockMovement is append-only")


class LowStockAlert(UUIDModel):
    stock_level = models.ForeignKey(StockLevel, on_delete=models.CASCADE, related_name="alerts")
    available_at_trigger = models.IntegerField()
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["stock_level"],
                condition=models.Q(resolved_at__isnull=True),
                name="one_open_alert_per_level",
            )
        ]
