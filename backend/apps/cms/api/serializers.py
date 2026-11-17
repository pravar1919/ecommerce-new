"""Public (resolved) CMS shapes. References are expanded server-side so the storefront makes one call.

Block output serializers exist mainly for the OpenAPI contract: the `Block` component is a
discriminated union on `type`, which openapi-typescript turns into a TS union.
"""

from drf_spectacular.utils import PolymorphicProxySerializer
from rest_framework import serializers

from apps.catalog.api.serializers import ProductCardSerializer

from ..blocks import ACCENTS


def _const(value: str) -> serializers.ChoiceField:
    return serializers.ChoiceField(choices=[value])


class MediaOutSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=["image", "video"])
    url = serializers.CharField()
    poster_url = serializers.CharField(allow_null=True)
    alt = serializers.CharField(allow_blank=True, help_text="Empty string means decorative")
    width = serializers.IntegerField(allow_null=True)
    height = serializers.IntegerField(allow_null=True)
    focal_x = serializers.FloatField()
    focal_y = serializers.FloatField()
    dominant_hex = serializers.CharField(allow_blank=True)
    blurhash = serializers.CharField(allow_blank=True)
    credit = serializers.CharField(allow_blank=True)
    is_placeholder = serializers.BooleanField()


class LinkOutSerializer(serializers.Serializer):
    label = serializers.CharField()
    href = serializers.CharField()


class RefSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()


class CategoryRefOutSerializer(RefSerializer):
    path = serializers.CharField()


# ---------- block configs (resolved) ------------------------------------------------------------
class HeroSlideOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    headline = serializers.CharField()
    subline = serializers.CharField(allow_blank=True)
    media = MediaOutSerializer()
    mobile_media = MediaOutSerializer(allow_null=True)
    cta = LinkOutSerializer(allow_null=True)
    secondary_cta = LinkOutSerializer(allow_null=True)
    accent = serializers.ChoiceField(choices=ACCENTS)
    theme = serializers.ChoiceField(choices=["light", "dark"])


class HeroOut(serializers.Serializer):
    slides = HeroSlideOut(many=True)
    autoplay_ms = serializers.IntegerField(allow_null=True)


class CategoryTileOut(serializers.Serializer):
    category = CategoryRefOutSerializer()
    media = MediaOutSerializer()
    label = serializers.CharField()


class CategoryGridOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    title = serializers.CharField()
    items = CategoryTileOut(many=True)


class CollectionRefOut(RefSerializer):
    eyebrow = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    accent = serializers.ChoiceField(choices=ACCENTS)


class CollectionFeatureOut(serializers.Serializer):
    collection = CollectionRefOut()
    layout = serializers.ChoiceField(choices=["split_left", "split_right", "full_bleed"])
    media = MediaOutSerializer(many=True)
    eyebrow = serializers.CharField(allow_blank=True)
    headline = serializers.CharField()
    body = serializers.CharField(allow_blank=True)
    cta_label = serializers.CharField()


class ProductRailOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    title = serializers.CharField()
    source = serializers.ChoiceField(choices=["collection", "manual", "new_arrivals", "trending"])
    collection_slug = serializers.CharField(allow_null=True)
    products = ProductCardSerializer(many=True)
    cta = LinkOutSerializer(allow_null=True)


class OccasionTileOut(serializers.Serializer):
    occasion = RefSerializer()
    media = MediaOutSerializer()
    label = serializers.CharField()


class OccasionTilesOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    title = serializers.CharField(allow_blank=True)
    items = OccasionTileOut(many=True)


class EditorialSplitOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    headline = serializers.CharField()
    body = serializers.CharField()
    media = MediaOutSerializer(many=True)
    cta = LinkOutSerializer(allow_null=True)
    layout = serializers.ChoiceField(choices=["7_5", "5_7", "overlap"])


class StatOut(serializers.Serializer):
    value = serializers.IntegerField()
    suffix = serializers.CharField(allow_blank=True)
    label = serializers.CharField()


class CraftStoryOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    headline = serializers.CharField()
    body = serializers.CharField()
    stats = StatOut(many=True)
    media = MediaOutSerializer(many=True)
    cta = LinkOutSerializer(allow_null=True)


class TestimonialOut(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    quote = serializers.CharField()
    occasion = serializers.CharField(allow_blank=True)
    location = serializers.CharField(allow_blank=True)
    media = MediaOutSerializer(allow_null=True)
    is_placeholder = serializers.BooleanField()


class TestimonialsOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    title = serializers.CharField(allow_blank=True)
    items = TestimonialOut(many=True)


class InstagramGalleryOut(serializers.Serializer):
    title = serializers.CharField(allow_blank=True)
    handle = serializers.CharField(allow_null=True)
    profile_url = serializers.CharField(allow_null=True)
    media = MediaOutSerializer(many=True)


class NewsletterOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    headline = serializers.CharField()
    body = serializers.CharField(allow_blank=True)
    consent_text = serializers.CharField(allow_blank=True)


class RichTextOut(serializers.Serializer):
    html = serializers.CharField(help_text="Sanitised server-side (nh3 allow-list)")


BLOCK_OUTPUTS = {
    "hero": HeroOut,
    "category_grid": CategoryGridOut,
    "collection_feature": CollectionFeatureOut,
    "product_rail": ProductRailOut,
    "occasion_tiles": OccasionTilesOut,
    "editorial_split": EditorialSplitOut,
    "craft_story": CraftStoryOut,
    "testimonials": TestimonialsOut,
    "instagram_gallery": InstagramGalleryOut,
    "newsletter": NewsletterOut,
    "rich_text": RichTextOut,
}


def _block_serializer(block_type: str, config_cls) -> type[serializers.Serializer]:
    camel = "".join(p.title() for p in block_type.split("_"))
    return type(
        f"{camel}Block",
        (serializers.Serializer,),
        {"id": serializers.UUIDField(), "type": _const(block_type), "config": config_cls()},
    )


BLOCK_SERIALIZERS = {t: _block_serializer(t, c) for t, c in BLOCK_OUTPUTS.items()}

BlockSerializer = PolymorphicProxySerializer(
    component_name="Block", serializers=BLOCK_SERIALIZERS, resource_type_field_name="type", many=True
)


class SeoOutSerializer(serializers.Serializer):
    title = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    og_image = MediaOutSerializer(allow_null=True)


class PageOutSerializer(serializers.Serializer):
    slug = serializers.CharField()
    title = serializers.CharField()
    template = serializers.ChoiceField(choices=["home", "landing", "content"])
    version = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["draft", "scheduled", "published", "archived"])
    published_at = serializers.DateTimeField(allow_null=True)
    seo = SeoOutSerializer()
    blocks = BlockSerializer


# ---------- site settings / navigation -------------------------------------------------------------
class AnnouncementMessageOut(serializers.Serializer):
    text = serializers.CharField()
    href = serializers.CharField(allow_null=True)


class AnnouncementOut(serializers.Serializer):
    enabled = serializers.BooleanField()
    accent = serializers.ChoiceField(choices=[*ACCENTS, "charcoal"])
    messages = AnnouncementMessageOut(many=True)


class FooterColumnOut(serializers.Serializer):
    title = serializers.CharField()
    links = LinkOutSerializer(many=True)


class FooterOut(serializers.Serializer):
    columns = FooterColumnOut(many=True)
    note = serializers.CharField(allow_blank=True)


class SocialLinkOut(serializers.Serializer):
    network = serializers.CharField()
    url = serializers.CharField()


class SiteSettingsOutSerializer(serializers.Serializer):
    brand_name = serializers.CharField()
    legal_name = serializers.CharField(allow_blank=True)
    tagline = serializers.CharField(allow_blank=True)
    monogram = serializers.CharField(allow_blank=True)
    logo = MediaOutSerializer(allow_null=True)
    theme_key = serializers.CharField()
    environment = serializers.CharField()
    is_dev_identity = serializers.BooleanField(
        help_text="True while the temporary development identity is in use"
    )
    support_email = serializers.CharField(allow_blank=True)
    support_phone = serializers.CharField(allow_blank=True)
    registered_address = serializers.CharField(allow_blank=True)
    social_links = SocialLinkOut(many=True)
    announcement = AnnouncementOut()
    footer = FooterOut()
    seo_title = serializers.CharField(allow_blank=True)
    seo_description = serializers.CharField(allow_blank=True)


class NavFeatureOut(serializers.Serializer):
    eyebrow = serializers.CharField(allow_blank=True)
    title = serializers.CharField()
    href = serializers.CharField()
    media = MediaOutSerializer()


class NavChildOut(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    path = serializers.CharField()


class NavItemOut(NavChildOut):
    eyebrow = serializers.CharField(allow_blank=True)
    children = NavChildOut(many=True)
    features = NavFeatureOut(many=True)


class NavCollectionOut(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.CharField()
    accent = serializers.CharField()


class NavigationOutSerializer(serializers.Serializer):
    items = NavItemOut(many=True)
    collections = NavCollectionOut(many=True)


# ---------- newsletter ------------------------------------------------------------------------------
class NewsletterSignupSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    consent = serializers.BooleanField(help_text="Must be true: explicit marketing consent")
    source = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")

    def validate_consent(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("Please confirm you'd like to receive our emails.")
        return value


class NewsletterTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=300)


class NewsletterStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["pending", "confirmed", "unsubscribed"])
