import pytest
from django.core.management import CommandError, call_command

from apps.catalog.api.serializers import ImageSerializer
from apps.catalog.models import ProductMedia
from apps.cms.models import MediaAsset
from apps.cms.selectors import media_dict

pytestmark = pytest.mark.django_db

UNSPLASH = "https://images.unsplash.com/"


@pytest.fixture
def seeded(settings):
    settings.ENVIRONMENT = "development"
    settings.UNSPLASH_ACCESS_KEY = ""
    call_command("seed_dev", verbosity=0)


def test_demo_photos_cover_every_placeholder_and_stay_flagged(seeded):
    call_command("seed_demo_photos", "--no-ping", verbosity=0)
    media = ProductMedia.objects.all()
    assert media.exists()
    # the manifest covers every seeded product colour slot, one unique photo each
    assert not media.filter(external_url="").exists()
    assert media.values("external_url").distinct().count() == media.count()
    # stock photos of similar garments, never presented as real product photography
    assert not media.filter(is_placeholder=False).exists()
    m = media.first()
    data = ImageSerializer(m).data
    assert data["url"].startswith(UNSPLASH)
    assert data["credit"] and data["credit_url"].startswith("https://unsplash.com/")

    assets = MediaAsset.objects.filter(tags__contains=["demo-stock"])
    assert assets.count() == MediaAsset.objects.count()
    a = assets.first()
    assert media_dict(a)["url"].startswith(UNSPLASH)
    assert "Unsplash" in a.usage_rights

    call_command("seed_demo_photos", "--no-ping", verbosity=0)  # idempotent
    assert ProductMedia.objects.count() == media.count()


def test_revert_restores_generated_placeholders(seeded):
    call_command("seed_demo_photos", "--no-ping", verbosity=0)
    call_command("seed_demo_photos", "--revert", verbosity=0)
    assert not ProductMedia.objects.exclude(external_url="").exists()
    assert not MediaAsset.objects.exclude(external_url="").exists()
    assert not MediaAsset.objects.filter(tags__contains=["demo-stock"]).exists()
    m = ProductMedia.objects.select_related("product").first()
    assert ImageSerializer(m).data["url"].endswith(".png")
    assert m.alt_text.startswith("Development placeholder for")


def test_missing_key_skips_download_tracking(seeded, capsys):
    call_command("seed_demo_photos")
    assert "download tracking skipped" in capsys.readouterr().out


def test_demo_photos_refuse_production(settings):
    settings.ENVIRONMENT = "production"
    with pytest.raises(CommandError):
        call_command("seed_demo_photos", "--no-ping", verbosity=0)
