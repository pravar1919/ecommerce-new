"""Development CMS content: site settings, navigation tiles, and the homepage (every section).

Rules this follows (architecture audit #8, #9):
- Campaign imagery is generated, labelled DEV PLACEHOLDER and flagged `is_placeholder`.
- No brand name is written here: SiteSettings is seeded from the env (dev identity ATELIER).
- Testimonials are flagged placeholders; the storefront labels them. Real ones need recorded consent.
- Copy makes no business claims beyond what the system actually does (GST-inclusive prices, MTM).
- Craft stats are computed from the seeded catalogue, not invented.
"""

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.attributes.models import EmbroideryType, Occasion
from apps.catalog.models import Product
from apps.categories.models import Category, Collection
from apps.cms import selectors as cms_selectors
from apps.cms import services as cms_services
from apps.cms.models import ContentBlock, MediaAsset, NavigationFeature, Page, PageVersion, Testimonial

# key, label, hex, (w, h)
CAMPAIGN_MEDIA = [
    ("hero-groom", "Campaign hero · The Groom Edit", "#651E35", (2520, 1080)),
    ("hero-groom-mobile", "Campaign hero (mobile) · The Groom Edit", "#651E35", (1200, 1500)),
    ("hero-sangeet", "Campaign hero · Sangeet Nights", "#263E80", (2520, 1080)),
    ("hero-sangeet-mobile", "Campaign hero (mobile) · Sangeet Nights", "#263E80", (1200, 1500)),
    ("cat-sherwanis", "Category tile · Sherwanis", "#3A3938", (1200, 1500)),
    ("cat-kurtas", "Category tile · Kurtas", "#D9C3A0", (1200, 1500)),
    ("cat-indo-western", "Category tile · Indo-Western", "#1D2742", (1200, 1500)),
    ("cat-suits", "Category tile · Suits & Blazers", "#242323", (1200, 1500)),
    ("cat-accessories", "Category tile · Accessories", "#9AAA8C", (1200, 1500)),
    ("groom-edit-1", "Collection · The Groom Edit (portrait)", "#651E35", (1200, 1600)),
    ("groom-edit-2", "Collection · The Groom Edit (detail)", "#C5A46D", (1200, 1800)),
    ("occ-wedding", "Occasion · Wedding", "#F2EBDD", (1200, 1500)),
    ("occ-sangeet", "Occasion · Sangeet", "#263E80", (1200, 1500)),
    ("occ-mehendi", "Occasion · Mehendi", "#9AAA8C", (1200, 1500)),
    ("occ-haldi", "Occasion · Haldi", "#E5A52B", (1200, 1500)),
    ("occ-reception", "Occasion · Reception", "#1E1D1D", (1200, 1500)),
    ("occ-festive", "Occasion · Festive", "#174B3B", (1200, 1500)),
    ("mtm-1", "Editorial · Made to measure (fitting)", "#E9E1D3", (1200, 1600)),
    ("mtm-2", "Editorial · Made to measure (detail)", "#6B655C", (1200, 1800)),
    ("craft-1", "Craft · Zardozi in progress", "#174B3B", (1600, 1200)),
    ("craft-2", "Craft · Hand-finishing", "#C5A46D", (1200, 1500)),
    *[
        (f"gram-{i}", f"Gallery tile {i}", hx, (1080, 1080))
        for i, hx in enumerate(
            ["#651E35", "#F2EBDD", "#174B3B", "#263E80", "#D9C3A0", "#3A3938", "#E8C4C0", "#9AAA8C"], start=1
        )
    ],
]
FOCAL = {"hero-groom": (0.7, 0.4), "hero-sangeet": (0.3, 0.4)}


def _media(images: bool, placeholder_png, log) -> dict[str, MediaAsset]:
    out = {}
    for i, (key, label, hx, size) in enumerate(CAMPAIGN_MEDIA):
        tag = f"seed:{key}"
        m = MediaAsset.objects.filter(tags__contains=[tag]).first()
        if m is None:
            fx, fy = FOCAL.get(key, (0.5, 0.5))
            m = MediaAsset(
                alt_text=f"Development placeholder: {label}",
                width=size[0],
                height=size[1],
                focal_x=fx,
                focal_y=fy,
                dominant_hex=hx,
                tags=[tag, "dev-placeholder"],
                usage_rights="Development only",
                is_placeholder=True,
            )
            content = (
                placeholder_png(label, hx, i, size=size, note="campaign placeholder")
                if images
                else b"placeholder"
            )
            m.file.save(f"dev-placeholder-{key}.png", ContentFile(content), save=False)
            m.save()
            if images:
                log(f"  cms media: {key}")
        out[key] = m
    return out


def _settings() -> None:
    s = cms_selectors.site_settings()
    changed = False
    if not s.announcement:
        s.announcement = {
            "enabled": True,
            "accent": "burgundy",
            "messages": [
                {
                    "text": "The Groom Edit: heirloom sherwanis, finished by hand",
                    "href": "/collections/the-groom-edit",
                },
                {"text": "Made-to-measure available on selected styles", "href": "/made-to-measure"},
                {"text": "All prices include GST", "href": None},
            ],
        }
        changed = True
    if not s.footer:
        s.footer = {
            "columns": [
                {
                    "title": "Shop",
                    "links": [
                        {"label": "Sherwanis", "href": "/sherwanis"},
                        {"label": "Kurtas", "href": "/kurtas"},
                        {"label": "Indo-Western", "href": "/indo-western"},
                        {"label": "Suits & Blazers", "href": "/suits-blazers"},
                        {"label": "Accessories", "href": "/accessories"},
                    ],
                },
                {
                    "title": "Edits",
                    "links": [
                        {"label": "The Groom Edit", "href": "/collections/the-groom-edit"},
                        {"label": "Sangeet Nights", "href": "/collections/sangeet-nights"},
                        {"label": "The Festive Edit", "href": "/collections/the-festive-edit"},
                    ],
                },
                {
                    "title": "Help",
                    "links": [
                        {"label": "Size guide", "href": "/size-guide"},
                        {"label": "Made to measure", "href": "/made-to-measure"},
                        {"label": "Track an order", "href": "/account/orders"},
                        {"label": "Contact us", "href": "/contact"},
                    ],
                },
            ],
            "note": "Prices are in Indian rupees and include GST.",
        }
        changed = True
    if not s.seo_description:
        s.seo_description = (
            "Occasion menswear for weddings and celebrations: sherwanis, kurtas and tailoring."
        )
        changed = True
    if changed:
        s.save()


def _navigation(media: dict) -> None:
    features = [
        ("sherwanis", "The edit", "The Groom Edit", "/collections/the-groom-edit", "groom-edit-1"),
        ("kurtas", "For the night before", "Sangeet Nights", "/collections/sangeet-nights", "occ-sangeet"),
        (
            "suits-blazers",
            "Season of celebrations",
            "The Festive Edit",
            "/collections/the-festive-edit",
            "craft-1",
        ),
    ]
    for i, (path, eyebrow, title, href, mkey) in enumerate(features):
        NavigationFeature.objects.get_or_create(
            category_path=path,
            title=title,
            defaults={"eyebrow": eyebrow, "href": href, "media": media[mkey], "position": i},
        )


def _testimonials() -> list[Testimonial]:
    rows = [
        (
            "Placeholder testimonial",
            "Wedding",
            "Real customer words appear here once a customer consents to share them.",
        ),
        (
            "Placeholder testimonial",
            "Reception",
            "Testimonials are added in the admin with consent recorded, never invented.",
        ),
        (
            "Placeholder testimonial",
            "Sangeet",
            "This card shows how a short quote, name and occasion sit together.",
        ),
    ]
    out = []
    for i, (name, occasion, quote) in enumerate(rows):
        t, _ = Testimonial.objects.get_or_create(
            name=f"{name} {i + 1}",
            defaults={"quote": quote, "occasion": occasion, "is_published": True, "is_placeholder": True},
        )
        out.append(t)
    return out


def _home_blocks(media: dict, testimonials: list[Testimonial]) -> list[tuple[str, dict]]:
    cat = {c.slug: str(c.id) for c in Category.objects.filter(depth=0)}
    occ = {o.slug: str(o.id) for o in Occasion.objects.all()}
    col = {c.slug: str(c.id) for c in Collection.objects.all()}
    m = {k: str(v.id) for k, v in media.items()}
    published = Product.objects.filter(status=Product.Status.PUBLISHED)
    techniques = EmbroideryType.objects.exclude(slug="none").count()
    mtm_days = (
        published.exclude(mtm_lead_time_days=None).values_list("mtm_lead_time_days", flat=True).first() or 21
    )
    return [
        (
            "hero",
            {
                "autoplay_ms": 7000,
                "slides": [
                    {
                        "eyebrow": "The Groom Edit",
                        "headline": "The art of being the groom",
                        "subline": "Heirloom sherwanis in raw silk and velvet, hand-finished with zardozi.",
                        "media": m["hero-groom"],
                        "mobile_media": m["hero-groom-mobile"],
                        "cta": {"label": "Shop the edit", "href": "/collections/the-groom-edit"},
                        "secondary_cta": {"label": "Made to measure", "href": "/made-to-measure"},
                        "accent": "burgundy",
                        "theme": "dark",
                    },
                    {
                        "eyebrow": "Sangeet Nights",
                        "headline": "Dressed for the night before",
                        "subline": "Jacquard kurta sets and draped silhouettes that move with you.",
                        "media": m["hero-sangeet"],
                        "mobile_media": m["hero-sangeet-mobile"],
                        "cta": {"label": "Explore Sangeet", "href": "/collections/sangeet-nights"},
                        "accent": "royal",
                        "theme": "dark",
                    },
                ],
            },
        ),
        (
            "category_grid",
            {
                "eyebrow": "The wardrobe",
                "title": "Dress for every ceremony",
                "items": [
                    {"category_id": cat["sherwanis"], "media": m["cat-sherwanis"]},
                    {"category_id": cat["kurtas"], "media": m["cat-kurtas"]},
                    {"category_id": cat["indo-western"], "media": m["cat-indo-western"]},
                    {"category_id": cat["suits-blazers"], "media": m["cat-suits"]},
                    {"category_id": cat["accessories"], "media": m["cat-accessories"]},
                ],
            },
        ),
        (
            "product_rail",
            {
                "eyebrow": "Just in",
                "title": "New this season",
                "source": "new_arrivals",
                "limit": 8,
                "cta": {"label": "View all new arrivals", "href": "/search?ordering=newest"},
            },
        ),
        (
            "collection_feature",
            {
                "collection_id": col["the-groom-edit"],
                "layout": "split_left",
                "media": [m["groom-edit-1"], m["groom-edit-2"]],
                "eyebrow": "Collection",
                "cta_label": "Explore the Groom Edit",
            },
        ),
        (
            "occasion_tiles",
            {
                "eyebrow": "Shop by occasion",
                "title": "One wedding, many moments",
                "items": [
                    {"occasion_id": occ[s], "media": m[f"occ-{s}"]}
                    for s in ("wedding", "sangeet", "mehendi", "haldi", "reception", "festive")
                ],
            },
        ),
        (
            "editorial_split",
            {
                "eyebrow": "Made to measure",
                "headline": "Cut for you, and only you",
                "body": (
                    "Selected sherwanis, bandhgalas and suits can be made to your measurements. "
                    "Share them once with our measurement guide and we tailor the piece to your frame, "
                    f"usually in about {mtm_days} days."
                ),
                "media": [m["mtm-1"], m["mtm-2"]],
                "cta": {"label": "How made to measure works", "href": "/made-to-measure"},
                "layout": "7_5",
            },
        ),
        (
            "product_rail",
            {
                "eyebrow": "Collection",
                "title": "The Festive Edit",
                "source": "collection",
                "collection_id": col["the-festive-edit"],
                "limit": 8,
                "cta": {"label": "Shop the Festive Edit", "href": "/collections/the-festive-edit"},
            },
        ),
        (
            "craft_story",
            {
                "eyebrow": "Craft",
                "headline": "The hand is the luxury",
                "body": (
                    "Zardozi, aari, resham and chikankari are slow crafts. Each technique is worked "
                    "by hand, then finished with the same care as the cut beneath it."
                ),
                "stats": [
                    {"value": techniques, "label": "embroidery techniques in the collection"},
                    {"value": published.count(), "label": "styles, each cut and finished by hand"},
                    {"value": Occasion.objects.count(), "label": "occasions dressed, haldi to reception"},
                    {"value": mtm_days, "suffix": " days", "label": "typical made-to-measure lead time"},
                ],
                "media": [m["craft-1"], m["craft-2"]],
            },
        ),
        (
            "testimonials",
            {
                "eyebrow": "In their words",
                "title": "Worn on the day",
                "testimonial_ids": [str(t.id) for t in testimonials],
            },
        ),
        (
            "instagram_gallery",
            {"title": "From the atelier", "media": [m[f"gram-{i}"] for i in range(1, 9)]},
        ),
        (
            "newsletter",
            {
                "eyebrow": "Letters",
                "headline": "New edits, first",
                "body": "Occasional letters on new collections and the craft behind them.",
                "consent_text": "I'd like to receive emails. Unsubscribe at any time.",
            },
        ),
    ]


def seed_cms(*, images: bool, placeholder_png, log) -> None:
    media = _media(images, placeholder_png, log)
    with transaction.atomic():
        _settings()
        _navigation(media)
        testimonials = _testimonials()
        page, _ = Page.objects.get_or_create(
            slug="home",
            defaults={
                "title": "Home",
                "template": Page.Template.HOME,
                "seo_title": "",
                "seo_description": "Occasion menswear for weddings and celebrations.",
            },
        )
        if page.versions.exists():
            return
        version = PageVersion.objects.create(page=page, note="dev seed")
        for i, (block_type, config) in enumerate(_home_blocks(media, testimonials)):
            ContentBlock.objects.create(page_version=version, type=block_type, position=i * 10, config=config)
        cms_services.publish_version(version)
        log(f"  cms: home page v{version.version} published at {timezone.now():%H:%M}")
