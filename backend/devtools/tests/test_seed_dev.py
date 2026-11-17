import pytest
from django.core.management import CommandError, call_command

from apps.catalog.models import Product, ProductMedia, ProductVariant
from apps.inventory.models import StockLevel

pytestmark = pytest.mark.django_db


def test_seed_is_idempotent_and_publishable(settings):
    settings.ENVIRONMENT = "development"
    call_command("seed_dev", "--no-images", verbosity=0)
    counts = (Product.objects.count(), ProductVariant.objects.count(), StockLevel.objects.count())
    call_command("seed_dev", "--no-images", verbosity=0)
    assert (Product.objects.count(), ProductVariant.objects.count(), StockLevel.objects.count()) == counts
    assert counts[0] == 23
    # without images nothing is published: publish_product requires an image
    assert not Product.objects.filter(status="published").exists()


def test_seed_images_are_labelled_placeholders(settings):
    settings.ENVIRONMENT = "development"
    call_command("seed_dev", verbosity=0)
    assert ProductMedia.objects.exists()
    assert not ProductMedia.objects.filter(is_placeholder=False).exists()
    assert Product.objects.filter(status="published").count() == 23
    # CMS: homepage with every section, placeholder campaign media and flagged testimonials only
    from apps.cms.models import MediaAsset, Testimonial
    from apps.cms.selectors import page_dict, published_version

    page = page_dict(published_version("home"))
    assert [b["type"] for b in page["blocks"]] == [
        "hero",
        "category_grid",
        "product_rail",
        "collection_feature",
        "occasion_tiles",
        "editorial_split",
        "product_rail",
        "craft_story",
        "testimonials",
        "instagram_gallery",
        "newsletter",
    ]
    assert not MediaAsset.objects.filter(is_placeholder=False).exists()
    assert not Testimonial.objects.filter(is_placeholder=False).exists()
    call_command("seed_dev", verbosity=0)  # idempotent: no second version
    assert published_version("home").page.versions.count() == 1


def test_seed_refuses_production(settings):
    settings.ENVIRONMENT = "production"
    with pytest.raises(CommandError):
        call_command("seed_dev", "--no-images", verbosity=0)
