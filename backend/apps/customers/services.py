from decimal import Decimal, InvalidOperation

from django.db import transaction

from apps.accounts import services as account_services
from apps.catalog.models import MeasurementDefinition
from common.exceptions import DomainError

from .models import Address, CustomerProfile, MeasurementProfile


class InvalidMeasurements(DomainError):
    code = "invalid_measurements"


def get_or_create_profile(user) -> CustomerProfile:
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile


@transaction.atomic
def register_customer(
    request, *, email, password, first_name="", last_name="", phone=None, marketing_opt_in=False
):
    user = account_services.create_user(
        email=email, password=password, first_name=first_name, last_name=last_name, phone=phone
    )
    CustomerProfile.objects.create(user=user, marketing_email_opt_in=marketing_opt_in)
    account_services.login_user(request, email=email, password=password)
    return user


@transaction.atomic
def save_address(profile: CustomerProfile, *, instance: Address | None = None, **data) -> Address:
    address = instance or Address(customer=profile)
    for k, v in data.items():
        setattr(address, k, v)
    has_any = profile.addresses.exists()
    if not has_any and instance is None:
        address.is_default_shipping = address.is_default_billing = True
    if address.is_default_shipping:
        profile.addresses.exclude(pk=address.pk).filter(is_default_shipping=True).update(
            is_default_shipping=False
        )
    if address.is_default_billing:
        profile.addresses.exclude(pk=address.pk).filter(is_default_billing=True).update(
            is_default_billing=False
        )
    address.save()
    return address


@transaction.atomic
def set_default_address(address: Address, *, shipping: bool = True, billing: bool = True) -> Address:
    profile = CustomerProfile.objects.select_for_update().get(pk=address.customer_id)
    if shipping:
        profile.addresses.filter(is_default_shipping=True).update(is_default_shipping=False)
        address.is_default_shipping = True
    if billing:
        profile.addresses.filter(is_default_billing=True).update(is_default_billing=False)
        address.is_default_billing = True
    address.save(update_fields=["is_default_shipping", "is_default_billing", "updated_at"])
    return address


def validate_body_measurements(values: dict) -> dict:
    """Validate keys against MeasurementDefinition (body) and their allowed cm ranges."""
    defs = {
        d.key: d
        for d in MeasurementDefinition.objects.exclude(applies_to=MeasurementDefinition.AppliesTo.GARMENT)
    }
    errors, clean = {}, {}
    for key, raw in values.items():
        d = defs.get(key)
        if d is None:
            errors[key] = "Unknown measurement."
            continue
        try:
            value = Decimal(str(raw)).quantize(Decimal("0.1"))
        except InvalidOperation, ValueError:
            errors[key] = "Must be a number in centimetres."
            continue
        if not (d.min_cm <= value <= d.max_cm):
            errors[key] = f"Must be between {d.min_cm} and {d.max_cm} cm."
            continue
        clean[key] = str(value)
    if errors:
        raise InvalidMeasurements("Some measurements are invalid.", fields=errors)
    if not clean:
        raise InvalidMeasurements("Provide at least one measurement.")
    return clean


def save_measurement_profile(
    profile: CustomerProfile, *, instance: MeasurementProfile | None = None, **data
) -> MeasurementProfile:
    if "body_measurements" in data:
        data["body_measurements"] = validate_body_measurements(data["body_measurements"])
    mp = instance or MeasurementProfile(customer=profile)
    for k, v in data.items():
        setattr(mp, k, v)
    mp.save()
    return mp
