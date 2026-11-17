from django.conf import settings
from django.db import models

from common.models import UUIDModel

from .states import STATE_CHOICES

PINCODE_RE = r"^[1-9][0-9]{5}$"
INDIAN_MOBILE_RE = r"^\+91[6-9][0-9]{9}$"
GSTIN_RE = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"


class CustomerProfile(UUIDModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile"
    )
    marketing_email_opt_in = models.BooleanField(default=False)
    marketing_sms_opt_in = models.BooleanField(default=False)
    preferred_size = models.CharField(max_length=20, blank=True)

    def __str__(self) -> str:
        return str(self.user)


class Address(UUIDModel):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=13, help_text="+91XXXXXXXXXX")
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    landmark = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=80)
    state_code = models.CharField(max_length=2, choices=STATE_CHOICES)
    pincode = models.CharField(max_length=6)
    country = models.CharField(max_length=2, default="IN", editable=False)
    gstin = models.CharField(max_length=15, blank=True, help_text="Optional, for B2B invoices")
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default_shipping", "-updated_at"]
        verbose_name_plural = "addresses"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(pincode__regex=PINCODE_RE), name="address_pincode_format"
            ),
            models.CheckConstraint(
                condition=models.Q(phone__regex=INDIAN_MOBILE_RE), name="address_phone_format"
            ),
            models.CheckConstraint(
                condition=models.Q(gstin="") | models.Q(gstin__regex=GSTIN_RE), name="address_gstin_format"
            ),
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_default_shipping=True),
                name="address_one_default_shipping",
            ),
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_default_billing=True),
                name="address_one_default_billing",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.full_name}, {self.city} {self.pincode}"


class MeasurementProfile(UUIDModel):
    """Body measurements (cm) for made-to-measure orders. Keys come from catalog.MeasurementDefinition."""

    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE, related_name="measurement_profiles"
    )
    label = models.CharField(max_length=80)
    body_measurements = models.JSONField(default=dict)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    posture_notes = models.TextField(blank=True)
    schema_version = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.label
