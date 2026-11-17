import datetime as dt

import pytest
from django.contrib.postgres.fields.ranges import DateRange
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.attributes.models import Colour, EmbroideryType, Fabric, Fit, Occasion, Size, SizeSystem
from apps.catalog.models import MeasurementDefinition, Product, ProductMedia, ProductVariant
from apps.categories.models import Category
from apps.customers.models import CustomerProfile
from apps.inventory.models import StockLevel, StockLocation
from apps.pricing.models import TaxClass, TaxRule

PASSWORD = "correct-horse-battery-9"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def csrf_api():
    """Client that enforces CSRF exactly like a browser would."""
    return APIClient(enforce_csrf_checks=True)


def make_user(email="asha@example.com", **extra) -> User:
    user = User.objects.create_user(email=email, password=PASSWORD, first_name="Asha", **extra)
    CustomerProfile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def user(db):
    return make_user()


@pytest.fixture
def other_user(db):
    return make_user("ravi@example.com")


@pytest.fixture
def auth_api(api, user):
    api.force_authenticate(user)
    return api


@pytest.fixture
def location(db):
    return StockLocation.objects.create(name="Main", code="main", state_code="27", is_default=True)


@pytest.fixture
def tax_class(db):
    tc = TaxClass.objects.create(name="Apparel", code="apparel")
    TaxRule.objects.create(
        tax_class=tc,
        threshold_paise=250_000,
        rate_below_bp=500,
        rate_above_bp=1800,
        effective=DateRange(dt.date(2025, 9, 22), None),
    )
    return tc


class CatalogBuilder:
    def __init__(self, tax_class, location):
        self.tax_class = tax_class
        self.location = location
        self.root = Category.objects.create(name="Sherwanis", slug="sherwanis")
        self.kurtas = Category.objects.create(name="Kurtas", slug="kurtas")
        self.kurta_sets = Category.objects.create(name="Kurta Sets", slug="kurta-sets", parent=self.kurtas)
        self.system = SizeSystem.objects.create(name="Chest", slug="chest")
        self.sizes = {
            lab: Size.objects.create(system=self.system, label=lab, sort_order=i)
            for i, lab in enumerate(["38", "40", "42"])
        }
        self.colours = {
            n: Colour.objects.create(name=n, slug=n.lower(), hex=h, family=f)
            for n, h, f in [
                ("Ivory", "#F2EBDD", "neutral"),
                ("Burgundy", "#651E35", "red"),
                ("Emerald", "#174B3B", "green"),
            ]
        }
        self.wedding = Occasion.objects.create(name="Wedding", slug="wedding")
        self.haldi = Occasion.objects.create(name="Haldi", slug="haldi")
        self.silk = Fabric.objects.create(name="Raw Silk", slug="raw-silk")
        self.linen = Fabric.objects.create(name="Linen", slug="linen")
        self.zardozi = EmbroideryType.objects.create(name="Zardozi", slug="zardozi")
        self.slim = Fit.objects.create(name="Slim", slug="slim")
        for key, lo, hi in [("chest", 76, 150), ("waist", 60, 140)]:
            MeasurementDefinition.objects.create(
                key=key, label=key.title(), applies_to="both", min_cm=lo, max_cm=hi
            )

    def product(
        self,
        name,
        *,
        category=None,
        colours=("Ivory",),
        sizes=("38", "40", "42"),
        mrp=50_000_00,
        sale=None,
        stock=5,
        publish=True,
        fulfilment="ready_to_wear",
        occasions=(),
        fabric=None,
        embroidery=None,
        image=True,
        days_ago=10,
        rank=1000,
    ):
        p = Product.objects.create(
            name=name,
            slug=name.lower().replace(" ", "-"),
            category=category or self.root,
            hsn_code="6203",
            tax_class=self.tax_class,
            fulfilment_type=fulfilment,
            merch_rank=rank,
            mtm_lead_time_days=21 if fulfilment != "ready_to_wear" else None,
            fabric=fabric,
            embroidery=embroidery,
            fit=self.slim,
            short_description=f"{name} short",
            description=f"{name} description",
        )
        p.occasions.set(occasions)
        for c in colours:
            for s in sizes:
                v = ProductVariant.objects.create(
                    product=p,
                    sku=f"{p.slug}-{c}-{s}".upper(),
                    colour=self.colours[c],
                    size=self.sizes[s],
                    mrp_paise=mrp,
                    sale_price_paise=sale,
                )
                StockLevel.objects.create(variant=v, location=self.location, on_hand=stock)
            if fulfilment != "ready_to_wear":
                ProductVariant.objects.create(
                    product=p,
                    sku=f"{p.slug}-{c}-MTM".upper(),
                    colour=self.colours[c],
                    size=None,
                    mrp_paise=mrp + 10_000_00,
                    inventory_policy=ProductVariant.InventoryPolicy.MADE_TO_ORDER,
                )
        if image:
            m = ProductMedia(
                product=p,
                colour=self.colours[colours[0]],
                role="primary",
                alt_text=f"{name} front",
                width=1600,
                height=2000,
            )
            m.file.save("front.png", ContentFile(b"png"), save=False)
            m.save()
        if publish:
            p.status = Product.Status.PUBLISHED
            p.published_at = timezone.now() - dt.timedelta(days=days_ago)
            p.save()
        from apps.catalog.services import update_search_vectors

        update_search_vectors([p.pk])
        return p


@pytest.fixture
def catalog(db, tax_class, location):
    return CatalogBuilder(tax_class, location)
