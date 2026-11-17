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


def test_seed_refuses_production(settings):
    settings.ENVIRONMENT = "production"
    with pytest.raises(CommandError):
        call_command("seed_dev", "--no-images", verbosity=0)
