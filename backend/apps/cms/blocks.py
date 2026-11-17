"""Typed config schemas for CMS blocks (stored shape: references are UUIDs).

Each `ContentBlock.type` has exactly one config serializer here. `validate_config` is called from
model `clean()` (Django Admin, Phase 6 page builder) and from services, so invalid JSON never
reaches the storefront. The *resolved* public shapes live in `api/serializers.py`.
"""

from typing import Any

import nh3
from rest_framework import serializers

ACCENTS = ["burgundy", "emerald", "royal"]

RICH_TEXT_TAGS = {"p", "h2", "h3", "h4", "strong", "em", "a", "ul", "ol", "li", "blockquote", "br", "hr"}


class BlockConfigError(Exception):
    def __init__(self, messages: Any) -> None:
        self.messages = messages
        super().__init__(str(messages))

    def flat(self) -> list[str]:
        """'slides.0.cta.href: Use a site path…' lines, for Django form errors."""
        out: list[str] = []

        def walk(node, prefix: str) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, f"{prefix}.{k}" if prefix else str(k))
            elif isinstance(node, list) and node and all(isinstance(x, str) for x in node):
                out.extend(f"{prefix}: {x}" if prefix else str(x) for x in node)
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    if v:
                        walk(v, f"{prefix}.{i}")
            else:
                out.append(f"{prefix}: {node}")

        walk(self.messages, "")
        return out


def _check_href(value: str) -> str:
    value = value.strip()
    if value.startswith("/") and not value.startswith("//"):
        return value
    if value.startswith("https://"):
        return value
    raise serializers.ValidationError("Use a site path starting with '/' or an https:// URL.")


class HrefField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 300)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return _check_href(super().to_internal_value(data))


class LinkConfig(serializers.Serializer):
    label = serializers.CharField(max_length=40)
    href = HrefField()


class MediaId(serializers.UUIDField):
    """Reference to a cms.MediaAsset (existence is checked at resolve time; missing → item hidden)."""

    def to_internal_value(self, data):
        return str(super().to_internal_value(data))


class HeroSlideConfig(serializers.Serializer):
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    headline = serializers.CharField(max_length=90)
    subline = serializers.CharField(max_length=200, required=False, allow_blank=True)
    media = MediaId()
    mobile_media = MediaId(required=False, allow_null=True)
    cta = LinkConfig(required=False, allow_null=True)
    secondary_cta = LinkConfig(required=False, allow_null=True)
    accent = serializers.ChoiceField(choices=ACCENTS, default="burgundy")
    theme = serializers.ChoiceField(choices=["light", "dark"], default="dark")


class HeroConfig(serializers.Serializer):
    slides = HeroSlideConfig(many=True, min_length=1, max_length=5)
    autoplay_ms = serializers.IntegerField(min_value=4000, max_value=20000, required=False, allow_null=True)


class CategoryTileConfig(serializers.Serializer):
    category_id = serializers.UUIDField(format="hex_verbose")
    media = MediaId()
    label = serializers.CharField(max_length=40, required=False, allow_blank=True)


class CategoryGridConfig(serializers.Serializer):
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    title = serializers.CharField(max_length=80)
    items = CategoryTileConfig(many=True, min_length=2, max_length=8)


class CollectionFeatureConfig(serializers.Serializer):
    collection_id = serializers.UUIDField(format="hex_verbose")
    layout = serializers.ChoiceField(choices=["split_left", "split_right", "full_bleed"])
    media = serializers.ListField(child=MediaId(), min_length=1, max_length=3)
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    headline = serializers.CharField(max_length=90, required=False, allow_blank=True)
    body = serializers.CharField(max_length=400, required=False, allow_blank=True)
    cta_label = serializers.CharField(max_length=40, required=False, allow_blank=True)


class ProductRailConfig(serializers.Serializer):
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    title = serializers.CharField(max_length=80)
    source = serializers.ChoiceField(choices=["collection", "manual", "new_arrivals", "trending"])
    collection_id = serializers.UUIDField(format="hex_verbose", required=False, allow_null=True)
    product_ids = serializers.ListField(
        child=serializers.UUIDField(format="hex_verbose"), required=False, max_length=24
    )
    limit = serializers.IntegerField(min_value=2, max_value=16, default=8)
    cta = LinkConfig(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["source"] == "collection" and not attrs.get("collection_id"):
            raise serializers.ValidationError({"collection_id": "Required when source is 'collection'."})
        if attrs["source"] == "manual" and not attrs.get("product_ids"):
            raise serializers.ValidationError({"product_ids": "Required when source is 'manual'."})
        return attrs


class OccasionTileConfig(serializers.Serializer):
    occasion_id = serializers.UUIDField(format="hex_verbose")
    media = MediaId()
    label = serializers.CharField(max_length=40, required=False, allow_blank=True)


class OccasionTilesConfig(serializers.Serializer):
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    title = serializers.CharField(max_length=80, required=False, allow_blank=True)
    items = OccasionTileConfig(many=True, min_length=2, max_length=8)


class EditorialSplitConfig(serializers.Serializer):
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    headline = serializers.CharField(max_length=120)
    body = serializers.CharField(max_length=1200)
    media = serializers.ListField(child=MediaId(), min_length=1, max_length=2)
    cta = LinkConfig(required=False, allow_null=True)
    layout = serializers.ChoiceField(choices=["7_5", "5_7", "overlap"], default="7_5")


class StatConfig(serializers.Serializer):
    value = serializers.IntegerField(min_value=0, max_value=10_000_000)
    suffix = serializers.CharField(max_length=8, required=False, allow_blank=True)
    label = serializers.CharField(max_length=80)


class CraftStoryConfig(serializers.Serializer):
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    headline = serializers.CharField(max_length=120)
    body = serializers.CharField(max_length=1500)
    stats = StatConfig(many=True, max_length=4, required=False)
    media = serializers.ListField(child=MediaId(), min_length=1, max_length=3)
    cta = LinkConfig(required=False, allow_null=True)


class TestimonialsConfig(serializers.Serializer):
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    title = serializers.CharField(max_length=80, required=False, allow_blank=True)
    testimonial_ids = serializers.ListField(
        child=serializers.UUIDField(format="hex_verbose"), min_length=1, max_length=8
    )


class InstagramGalleryConfig(serializers.Serializer):
    title = serializers.CharField(max_length=80, required=False, allow_blank=True)
    handle = serializers.RegexField(
        r"^@?[A-Za-z0-9._]{1,30}$",
        max_length=31,
        required=False,
        allow_blank=True,
        help_text="Brand's own account; leave empty until the handle is confirmed",
    )
    media = serializers.ListField(child=MediaId(), min_length=3, max_length=12)


class NewsletterConfig(serializers.Serializer):
    eyebrow = serializers.CharField(max_length=60, required=False, allow_blank=True)
    headline = serializers.CharField(max_length=120)
    body = serializers.CharField(max_length=300, required=False, allow_blank=True)
    consent_text = serializers.CharField(max_length=300, required=False, allow_blank=True)


class RichTextConfig(serializers.Serializer):
    html = serializers.CharField(max_length=20_000)

    def validate_html(self, value: str) -> str:
        return nh3.clean(
            value,
            tags=RICH_TEXT_TAGS,
            attributes={"a": {"href", "title"}},
            url_schemes={"https", "mailto"},
            link_rel="noopener noreferrer",
        )


CONFIG_SERIALIZERS: dict[str, type[serializers.Serializer]] = {
    "hero": HeroConfig,
    "category_grid": CategoryGridConfig,
    "collection_feature": CollectionFeatureConfig,
    "product_rail": ProductRailConfig,
    "occasion_tiles": OccasionTilesConfig,
    "editorial_split": EditorialSplitConfig,
    "craft_story": CraftStoryConfig,
    "testimonials": TestimonialsConfig,
    "instagram_gallery": InstagramGalleryConfig,
    "newsletter": NewsletterConfig,
    "rich_text": RichTextConfig,
}


def _plain(value):
    """Serializer output → JSON-safe primitives (OrderedDict/UUID → dict/str)."""
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if value.__class__.__name__ == "UUID":
        return str(value)
    return value


def validate_config(block_type: str, config: dict) -> dict:
    """Validate and normalise a block config. Raises BlockConfigError with field messages."""
    serializer_cls = CONFIG_SERIALIZERS.get(block_type)
    if serializer_cls is None:
        raise BlockConfigError({"type": [f"Unknown block type '{block_type}'."]})
    s = serializer_cls(data=config or {})
    if not s.is_valid():
        raise BlockConfigError(s.errors)
    return _plain(s.validated_data)
