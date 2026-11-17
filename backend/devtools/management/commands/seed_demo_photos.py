"""Swap the labelled DEV PLACEHOLDER imagery for curated Unsplash photography, for client demos.

The photos come from a fixed manifest (devtools/demo_photos.json) that was picked by hand. They are
*stock photos of similar garments*, not this catalogue's products, so every row stays
`is_placeholder=True`, and product media is tagged with the photographer credit.

Unsplash API guidelines are followed: images are hotlinked from images.unsplash.com (stored as
`external_url`, never copied into our bucket), photographers are credited, and each photo's
`download_location` is pinged once when it is first used. Pings need UNSPLASH_ACCESS_KEY. When the
hourly rate limit is hit, the command reports how many are left; rerun it later to finish.

`--revert` puts the generated placeholders back (their files are never deleted).
"""

import json
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Product, ProductMedia
from apps.cms.models import MediaAsset
from apps.cms.services import NAVIGATION_TAG, SITE_SETTINGS_TAG, page_tag
from common.tasks import request_revalidation

MANIFEST = Path(__file__).resolve().parents[2] / "demo_photos.json"
PINGED_KEY = "devtools:demo-photos:pinged"
TAG = "demo-stock"
RIGHTS = "Unsplash License · demo only, not product photography"


class Command(BaseCommand):
    help = "Use curated Unsplash demo photography instead of placeholders (dev only, idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--revert", action="store_true", help="Restore the generated placeholders")
        parser.add_argument("--no-ping", action="store_true", help="Skip Unsplash download tracking")

    def handle(self, *args, **opts):
        if settings.ENVIRONMENT == "production":
            raise CommandError("seed_demo_photos refuses to run with ENVIRONMENT=production.")
        manifest = json.loads(MANIFEST.read_text())
        with transaction.atomic():
            if opts["revert"]:
                self.revert()
            else:
                self.apply_products(manifest["products"])
                self.apply_cms(manifest["cms"])
            request_revalidation(
                SITE_SETTINGS_TAG, NAVIGATION_TAG, page_tag("home"), "catalog:products", "catalog:categories"
            )
        if not opts["revert"] and not opts["no_ping"]:
            self.ping_downloads(manifest)

    # ---------- apply ---------------------------------------------------------------------------
    def apply_products(self, products: dict) -> None:
        n = 0
        for name, colours in products.items():
            product = Product.objects.filter(name=name).first()
            if product is None:
                self.stdout.write(self.style.WARNING(f"  skip: no product named {name!r}"))
                continue
            for colour, photos in colours.items():
                rows = list(product.media.filter(colour__name=colour, kind="image").order_by("position"))
                if len(rows) != len(photos):
                    msg = f"  {name} · {colour}: {len(rows)} media rows, {len(photos)} photos"
                    self.stdout.write(self.style.WARNING(msg))
                for row, photo in zip(rows, photos, strict=False):
                    row.external_url = photo["url"]
                    row.width, row.height = photo["width"], photo["height"]
                    row.alt_text = photo["alt"][:200]
                    row.credit, row.credit_url = photo["photographer"][:120], photo["photographer_url"]
                    row.focal_x, row.focal_y = photo.get("focal", (0.5, 0.35))
                    row.is_placeholder = True
                    row.save()
                    n += 1
        self.stdout.write(f"  product images: {n}")

    def apply_cms(self, slots: dict) -> None:
        n = 0
        for key, photo in slots.items():
            asset = MediaAsset.objects.filter(tags__contains=[f"seed:{key}"]).first()
            if asset is None:
                self.stdout.write(self.style.WARNING(f"  skip: no CMS media seeded for {key!r}"))
                continue
            asset.external_url = photo["url"]
            asset.width, asset.height = photo["width"], photo["height"]
            asset.alt_text = photo["alt"][:200]
            asset.credit, asset.credit_url = photo["photographer"][:120], photo["photographer_url"]
            asset.dominant_hex = photo["color"][:7]
            asset.blurhash = photo["blur_hash"][:100]
            asset.usage_rights = RIGHTS
            asset.tags = sorted({*asset.tags, TAG})
            asset.save()
            n += 1
        self.stdout.write(f"  CMS images: {n}")

    def revert(self) -> None:
        n = ProductMedia.objects.exclude(external_url="").update(
            external_url="", credit="", credit_url="", width=1600, height=2000, focal_x=0.5, focal_y=0.5
        )
        for p in ProductMedia.objects.filter(is_placeholder=True).select_related("product", "colour"):
            colour = p.colour.name if p.colour else "all colours"
            p.alt_text = f"Development placeholder for {p.product.name} in {colour}"
            p.save(update_fields=["alt_text"])
        m = 0
        for a in MediaAsset.objects.filter(tags__contains=[TAG]):
            from devtools.cms_seed import CAMPAIGN_MEDIA

            meta = {f"seed:{k}": (label, hx, size) for k, label, hx, size in CAMPAIGN_MEDIA}
            seed_tag = next((t for t in a.tags if t in meta), None)
            if seed_tag:
                label, hx, (w, h) = meta[seed_tag]
                a.alt_text, a.dominant_hex, a.width, a.height = f"Development placeholder: {label}", hx, w, h
            a.external_url, a.credit, a.credit_url, a.blurhash = "", "", "", ""
            a.usage_rights = "Development only"
            a.tags = [t for t in a.tags if t != TAG]
            a.save()
            m += 1
        self.stdout.write(f"  reverted: {n} product images, {m} CMS images")

    # ---------- Unsplash download tracking ------------------------------------------------------
    def ping_downloads(self, manifest: dict) -> None:
        key = settings.UNSPLASH_ACCESS_KEY
        photos = {
            p["id"]: p["download_location"]
            for colours in manifest["products"].values()
            for ps in colours.values()
            for p in ps
        } | {p["id"]: p["download_location"] for p in manifest["cms"].values()}
        pinged = set(cache.get(PINGED_KEY) or [])
        todo = [(i, url) for i, url in photos.items() if i not in pinged]
        if not todo:
            self.stdout.write("  Unsplash download tracking: complete")
            return
        if not key:
            self.stdout.write(self.style.WARNING("  UNSPLASH_ACCESS_KEY unset: download tracking skipped"))
            return
        for photo_id, url in todo:
            req = urllib.request.Request(  # noqa: S310  (URL from our own manifest, Unsplash API host)
                url, headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"}
            )
            try:
                with urllib.request.urlopen(req, timeout=15):  # noqa: S310
                    pinged.add(photo_id)
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    break  # hourly rate limit
                raise
        cache.set(PINGED_KEY, sorted(pinged), timeout=None)
        left = len(photos) - len(pinged & photos.keys())
        msg = f"  Unsplash download tracking: {len(photos) - left}/{len(photos)} recorded"
        if left:
            msg += f" ({left} left after the rate limit; rerun `make demo-photos` in an hour)"
        self.stdout.write(msg)
