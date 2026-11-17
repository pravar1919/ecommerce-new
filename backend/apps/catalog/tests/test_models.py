import pytest
from django.db import IntegrityError, transaction

from apps.catalog.models import Product, ProductVariant
from apps.catalog.services import publish_product
from common.exceptions import InvalidOperation

pytestmark = pytest.mark.django_db


def variant(p, catalog, **kw):
    data = {
        "product": p,
        "sku": "SKU-X",
        "colour": catalog.colours["Ivory"],
        "size": catalog.sizes["40"],
        "mrp_paise": 1000_00,
    }
    data.update(kw)
    return ProductVariant.objects.create(**data)


@pytest.mark.parametrize(
    "kw",
    [
        {"mrp_paise": 0},
        {"sale_price_paise": 1000_00},  # sale must be below MRP
        {"sale_price_paise": 0},
        {"size": None},  # tracked stock requires a size
    ],
)
def test_variant_constraints(catalog, kw):
    p = catalog.product("Plain", sizes=(), publish=False, image=False)
    with pytest.raises(IntegrityError), transaction.atomic():
        variant(p, catalog, **kw)


def test_variant_combo_unique_including_null_size(catalog):
    p = catalog.product("Combo", sizes=(), publish=False, image=False)
    variant(p, catalog)
    with pytest.raises(IntegrityError), transaction.atomic():
        variant(p, catalog, sku="SKU-Y")
    mtm = {"size": None, "inventory_policy": ProductVariant.InventoryPolicy.MADE_TO_ORDER}
    variant(p, catalog, sku="MTM-1", **mtm)
    with pytest.raises(IntegrityError), transaction.atomic():
        variant(p, catalog, sku="MTM-2", **mtm)  # NULLS NOT DISTINCT


def test_product_and_variant_are_distinct_entities(catalog):
    p = catalog.product("Distinct", colours=("Ivory", "Burgundy"), sizes=("38", "40"))
    assert p.variants.count() == 4
    assert {v.label for v in p.variants.select_related("colour", "size")} >= {"Ivory / 38", "Burgundy / 40"}


def test_publish_requires_variant_and_image(catalog):
    no_img = catalog.product("No Image", publish=False, image=False)
    with pytest.raises(InvalidOperation):
        publish_product(no_img)
    no_var = catalog.product("No Variant", sizes=(), publish=False)
    with pytest.raises(InvalidOperation):
        publish_product(no_var)
    ok = catalog.product("Ready", publish=False)
    publish_product(ok)
    ok.refresh_from_db()
    assert ok.status == Product.Status.PUBLISHED and ok.published_at is not None


def test_published_requires_date_in_db(catalog):
    p = catalog.product("Undated", publish=False)
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.filter(pk=p.pk).update(status="published", published_at=None)


def test_category_paths_cascade_on_move(catalog):
    catalog.kurtas.slug = "kurta-edit"
    catalog.kurtas.save()
    catalog.kurta_sets.refresh_from_db()
    assert catalog.kurta_sets.path == "kurta-edit/kurta-sets" and catalog.kurta_sets.depth == 1
