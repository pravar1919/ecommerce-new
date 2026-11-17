"""Read side: site settings, navigation, and published pages with every reference resolved.

Resolution is defensive: a reference to something deleted, unpublished or out of its window
silently drops that item, and a block left with nothing to show is omitted. The storefront never
renders a broken section because an editor archived a collection.
"""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.attributes.models import Occasion
from apps.catalog import selectors as catalog_selectors
from apps.catalog.api.serializers import ProductCardSerializer
from apps.categories import selectors as category_selectors

from .models import ContentBlock, MediaAsset, NavigationFeature, Page, PageVersion, SiteSettings, Testimonial

SOCIAL_ORDER = ["instagram", "youtube", "facebook", "pinterest", "whatsapp", "x"]


# ---------- media -------------------------------------------------------------------------------
def media_dict(m: MediaAsset) -> dict:
    return {
        "id": str(m.id),
        "kind": m.kind,
        "url": m.file.url,
        "poster_url": m.poster.url if m.poster else None,
        "alt": "" if m.is_decorative else m.alt_text,
        "width": m.width,
        "height": m.height,
        "focal_x": m.focal_x,
        "focal_y": m.focal_y,
        "dominant_hex": m.dominant_hex,
        "blurhash": m.blurhash,
        "credit": m.credit,
        "is_placeholder": m.is_placeholder,
    }


def parse_uuids(values: Iterable[Any]) -> set[str]:
    out = set()
    for v in values:
        try:
            out.add(str(UUID(str(v))))
        except ValueError, TypeError:
            continue
    return out


# ---------- site settings -------------------------------------------------------------------------
def site_settings() -> SiteSettings:
    obj = SiteSettings.objects.select_related("logo").filter(pk=1).first()
    if obj is None:
        # First boot: seed from env (brand-identity.md). Admins own the row afterwards.
        obj, _ = SiteSettings.objects.get_or_create(
            pk=1,
            defaults={
                "brand_name": settings.BRAND_NAME,
                "tagline": getattr(settings, "BRAND_TAGLINE", ""),
                "theme_key": settings.BRAND_THEME,
                "seller_state_code": settings.SELLER_STATE_CODE,
            },
        )
    return obj


def site_settings_dict() -> dict:
    s = site_settings()
    ann = s.announcement or {}
    messages = [
        {"text": str(m.get("text", ""))[:140], "href": m.get("href") or None}
        for m in ann.get("messages", [])
        if isinstance(m, dict) and m.get("text")
    ]
    footer = s.footer or {}
    columns = [
        {
            "title": str(c.get("title", "")),
            "links": [
                {"label": str(link.get("label", "")), "href": str(link.get("href", ""))}
                for link in c.get("links", [])
                if isinstance(link, dict) and link.get("label") and link.get("href")
            ],
        }
        for c in footer.get("columns", [])
        if isinstance(c, dict) and c.get("title")
    ]
    social = s.social_links or {}
    socials = sorted(
        (
            {"network": k, "url": v}
            for k, v in social.items()
            if isinstance(v, str) and v.startswith("https://")
        ),
        key=lambda x: SOCIAL_ORDER.index(x["network"]) if x["network"] in SOCIAL_ORDER else 99,
    )
    return {
        "brand_name": s.brand_name,
        "legal_name": s.legal_name,
        "tagline": s.tagline,
        "monogram": s.monogram,
        "logo": media_dict(s.logo) if s.logo else None,
        "theme_key": s.theme_key,
        "environment": settings.ENVIRONMENT,
        "is_dev_identity": s.brand_name == settings.DEV_BRAND_NAME,
        "support_email": s.support_email,
        "support_phone": s.support_phone,
        "registered_address": s.registered_address,
        "social_links": socials,
        "announcement": {
            "enabled": bool(ann.get("enabled")) and bool(messages),
            "accent": ann.get("accent")
            if ann.get("accent") in ("burgundy", "emerald", "royal")
            else "charcoal",
            "messages": messages,
        },
        "footer": {"columns": columns, "note": str(footer.get("note", ""))},
        "seo_title": s.seo_title,
        "seo_description": s.seo_description,
    }


# ---------- navigation ---------------------------------------------------------------------------
def navigation_dict() -> dict:
    cats = list(category_selectors.active_categories().filter(depth__lte=1))
    roots = [c for c in cats if c.parent_id is None]
    children: dict = {}
    for c in cats:
        if c.parent_id:
            children.setdefault(c.parent_id, []).append(c)
    features: dict[str, list] = {}
    for f in NavigationFeature.objects.filter(is_active=True).select_related("media"):
        features.setdefault(f.category_path, []).append(
            {"eyebrow": f.eyebrow, "title": f.title, "href": f.href, "media": media_dict(f.media)}
        )
    return {
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "path": r.path,
                "eyebrow": r.eyebrow,
                "children": [
                    {"id": str(c.id), "name": c.name, "path": c.path} for c in children.get(r.id, [])
                ],
                "features": features.get(r.path, [])[:2],
            }
            for r in roots
        ],
        "collections": [
            {"name": c.name, "slug": c.slug, "accent": c.accent}
            for c in category_selectors.live_collections()[:6]
        ],
    }


# ---------- pages ----------------------------------------------------------------------------------
def published_version(slug: str) -> PageVersion | None:
    return (
        PageVersion.objects.filter(page__slug=slug, status=PageVersion.Status.PUBLISHED)
        .select_related("page__og_image")
        .first()
    )


def visible_blocks(version: PageVersion, *, now=None) -> list[ContentBlock]:
    now = now or timezone.now()
    return list(
        version.blocks.filter(
            Q(visible_from__isnull=True) | Q(visible_from__lte=now),
            Q(visible_until__isnull=True) | Q(visible_until__gt=now),
        ).order_by("position", "created_at")
    )


def _link(value) -> dict | None:
    if isinstance(value, dict) and value.get("label") and value.get("href"):
        return {"label": value["label"], "href": value["href"]}
    return None


class _Resolver:
    """Batch-loads every referenced object across all blocks of a page (one query per model)."""

    def __init__(self, blocks: list[ContentBlock]) -> None:
        media_ids, cat_ids, occ_ids, col_ids, testimonial_ids = set(), set(), set(), set(), set()
        for b in blocks:
            c = b.config or {}
            match b.type:
                case "hero":
                    for s in c.get("slides", []):
                        media_ids |= parse_uuids([s.get("media"), s.get("mobile_media")])
                case "category_grid":
                    for i in c.get("items", []):
                        media_ids |= parse_uuids([i.get("media")])
                        cat_ids |= parse_uuids([i.get("category_id")])
                case "occasion_tiles":
                    for i in c.get("items", []):
                        media_ids |= parse_uuids([i.get("media")])
                        occ_ids |= parse_uuids([i.get("occasion_id")])
                case "collection_feature":
                    media_ids |= parse_uuids(c.get("media", []))
                    col_ids |= parse_uuids([c.get("collection_id")])
                case "product_rail":
                    col_ids |= parse_uuids([c.get("collection_id")])
                case "editorial_split" | "craft_story" | "instagram_gallery":
                    media_ids |= parse_uuids(c.get("media", []))
                case "testimonials":
                    testimonial_ids |= parse_uuids(c.get("testimonial_ids", []))
        testimonials = {
            str(t.id): t
            for t in Testimonial.objects.filter(pk__in=testimonial_ids, is_published=True).select_related(
                "media"
            )
        }
        media_ids |= {str(t.media_id) for t in testimonials.values() if t.media_id}
        self.media = {str(m.id): media_dict(m) for m in MediaAsset.objects.filter(pk__in=media_ids)}
        self.categories = {
            str(c.id): c for c in category_selectors.active_categories().filter(pk__in=cat_ids)
        }
        self.occasions = {str(o.id): o for o in Occasion.objects.filter(pk__in=occ_ids)}
        self.collections = {
            str(c.id): c for c in category_selectors.live_collections().filter(pk__in=col_ids)
        }
        self.testimonial_rows = testimonials

    def m(self, ref) -> dict | None:
        return self.media.get(str(ref)) if ref else None

    def ms(self, refs) -> list[dict]:
        return [x for x in (self.m(r) for r in refs or []) if x]

    # Each resolver returns the resolved config, or None to omit the block.
    def hero(self, c: dict) -> dict | None:
        slides = []
        for s in c.get("slides", []):
            media = self.m(s.get("media"))
            if not media:
                continue
            slides.append(
                {
                    "eyebrow": s.get("eyebrow", ""),
                    "headline": s["headline"],
                    "subline": s.get("subline", ""),
                    "media": media,
                    "mobile_media": self.m(s.get("mobile_media")),
                    "cta": _link(s.get("cta")),
                    "secondary_cta": _link(s.get("secondary_cta")),
                    "accent": s.get("accent", "burgundy"),
                    "theme": s.get("theme", "dark"),
                }
            )
        return {"slides": slides, "autoplay_ms": c.get("autoplay_ms")} if slides else None

    def category_grid(self, c: dict) -> dict | None:
        items = []
        for i in c.get("items", []):
            cat, media = self.categories.get(str(i.get("category_id"))), self.m(i.get("media"))
            if cat and media:
                items.append(
                    {
                        "category": {"id": str(cat.id), "name": cat.name, "slug": cat.slug, "path": cat.path},
                        "media": media,
                        "label": i.get("label") or cat.name,
                    }
                )
        return (
            {"eyebrow": c.get("eyebrow", ""), "title": c["title"], "items": items}
            if len(items) >= 2
            else None
        )

    def occasion_tiles(self, c: dict) -> dict | None:
        items = []
        for i in c.get("items", []):
            occ, media = self.occasions.get(str(i.get("occasion_id"))), self.m(i.get("media"))
            if occ and media:
                items.append(
                    {
                        "occasion": {"id": str(occ.id), "name": occ.name, "slug": occ.slug},
                        "media": media,
                        "label": i.get("label") or occ.name,
                    }
                )
        if len(items) < 2:
            return None
        return {"eyebrow": c.get("eyebrow", ""), "title": c.get("title", ""), "items": items}

    def collection_feature(self, c: dict) -> dict | None:
        col, media = self.collections.get(str(c.get("collection_id"))), self.ms(c.get("media"))
        if not col or not media:
            return None
        return {
            "collection": {
                "id": str(col.id),
                "name": col.name,
                "slug": col.slug,
                "eyebrow": col.eyebrow,
                "description": col.description,
                "accent": col.accent,
            },
            "layout": c.get("layout", "split_left"),
            "media": media,
            "eyebrow": c.get("eyebrow") or col.eyebrow,
            "headline": c.get("headline") or col.name,
            "body": c.get("body") or col.description,
            "cta_label": c.get("cta_label") or "Explore the edit",
        }

    def product_rail(self, c: dict) -> dict | None:
        limit = int(c.get("limit") or 8)
        source = c.get("source")
        collection_slug = None
        if source == "manual":
            ids = [i for i in c.get("product_ids", []) if parse_uuids([i])]
            by_id = {str(p.pk): p for p in catalog_selectors.products_by_ids(ids)}
            products = [by_id[str(i)] for i in ids if str(i) in by_id][:limit]
        else:
            f = catalog_selectors.ProductFilters()
            if source == "collection":
                col = self.collections.get(str(c.get("collection_id")))
                if not col:
                    return None
                f.collection = collection_slug = col.slug
            f.ordering = {"new_arrivals": "newest", "trending": "bestselling"}.get(source, "featured")
            f.in_stock = source in ("new_arrivals", "trending")
            products = list(catalog_selectors.list_products(f)[:limit])
        if not products:
            return None
        return {
            "eyebrow": c.get("eyebrow", ""),
            "title": c["title"],
            "source": source,
            "collection_slug": collection_slug,
            "products": ProductCardSerializer(products, many=True).data,
            "cta": _link(c.get("cta")),
        }

    def editorial_split(self, c: dict) -> dict | None:
        media = self.ms(c.get("media"))
        if not media:
            return None
        return {
            "eyebrow": c.get("eyebrow", ""),
            "headline": c["headline"],
            "body": c["body"],
            "media": media,
            "cta": _link(c.get("cta")),
            "layout": c.get("layout", "7_5"),
        }

    def craft_story(self, c: dict) -> dict | None:
        media = self.ms(c.get("media"))
        if not media:
            return None
        return {
            "eyebrow": c.get("eyebrow", ""),
            "headline": c["headline"],
            "body": c["body"],
            "stats": [
                {"value": s["value"], "suffix": s.get("suffix", ""), "label": s["label"]}
                for s in c.get("stats", [])
            ],
            "media": media,
            "cta": _link(c.get("cta")),
        }

    def testimonials(self, c: dict) -> dict | None:
        items = []
        for tid in c.get("testimonial_ids", []):
            t = self.testimonial_rows.get(str(tid))
            if t:
                items.append(
                    {
                        "id": str(t.id),
                        "name": t.name,
                        "quote": t.quote,
                        "occasion": t.occasion,
                        "location": t.location,
                        "media": self.m(t.media_id),
                        "is_placeholder": t.is_placeholder,
                    }
                )
        if not items:
            return None
        return {"eyebrow": c.get("eyebrow", ""), "title": c.get("title", ""), "items": items}

    def instagram_gallery(self, c: dict) -> dict | None:
        media = self.ms(c.get("media"))
        if len(media) < 3:
            return None
        handle = (c.get("handle") or "").lstrip("@")
        return {
            "title": c.get("title", ""),
            "handle": f"@{handle}" if handle else None,
            "profile_url": f"https://www.instagram.com/{handle}/" if handle else None,
            "media": media,
        }

    def newsletter(self, c: dict) -> dict | None:
        return {
            "eyebrow": c.get("eyebrow", ""),
            "headline": c["headline"],
            "body": c.get("body", ""),
            "consent_text": c.get("consent_text", ""),
        }

    def rich_text(self, c: dict) -> dict | None:
        return {"html": c["html"]} if c.get("html") else None


def resolve_blocks(blocks: list[ContentBlock]) -> list[dict]:
    r = _Resolver(blocks)
    out = []
    for b in blocks:
        resolver = getattr(r, b.type, None)
        config = resolver(b.config or {}) if resolver else None
        if config is not None:
            out.append({"id": str(b.id), "type": b.type, "config": config})
    return out


def page_dict(version: PageVersion) -> dict:
    page: Page = version.page
    return {
        "slug": page.slug,
        "title": page.title,
        "template": page.template,
        "version": version.version,
        "status": version.status,
        "published_at": version.published_at,
        "seo": {
            "title": page.seo_title,
            "description": page.seo_description,
            "og_image": media_dict(page.og_image) if page.og_image else None,
        },
        "blocks": resolve_blocks(visible_blocks(version)),
    }
