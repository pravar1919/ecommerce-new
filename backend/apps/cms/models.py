"""Content: brand settings, campaign media library, versioned pages built from typed blocks.

Brand identity is data (docs/brand-identity.md): nothing brand-specific is hardcoded in code.
Campaign/editorial media live here and are never product photography (architecture audit #8).
"""

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from common.models import TimeStampedModel, UUIDModel


class Accent(models.TextChoices):
    BURGUNDY = "burgundy", "Burgundy"
    EMERALD = "emerald", "Emerald"
    ROYAL = "royal", "Royal blue"


class ThemeKey(models.TextChoices):
    HEIRLOOM = "heirloom", "Quiet Heirloom (approved)"
    DEV = "dev", "Development"


def cms_media_path(instance: MediaAsset, filename: str) -> str:
    return f"cms/{timezone.now():%Y/%m}/{instance.id}/{filename}"


class MediaAsset(UUIDModel):
    """Campaign / editorial library. Never attached to products (is_product_photo is always false)."""

    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    kind = models.CharField(max_length=5, choices=Kind.choices, default=Kind.IMAGE)
    file = models.FileField(upload_to=cms_media_path, max_length=300, blank=True)
    external_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Hotlinked image (e.g. Unsplash demo stock). Takes precedence over the uploaded file.",
    )
    poster = models.FileField(upload_to=cms_media_path, max_length=300, blank=True, help_text="Video poster")
    alt_text = models.CharField(
        max_length=200, blank=True, help_text="Required for meaningful images; leave empty only if decorative"
    )
    is_decorative = models.BooleanField(default=False, help_text="Rendered with alt=''")
    credit = models.CharField(max_length=120, blank=True)
    credit_url = models.URLField(max_length=300, blank=True)
    usage_rights = models.CharField(max_length=200, blank=True, help_text="Licence / expiry of usage rights")
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    focal_x = models.FloatField(default=0.5)
    focal_y = models.FloatField(default=0.5)
    blurhash = models.CharField(max_length=100, blank=True)
    dominant_hex = models.CharField(max_length=7, blank=True, help_text="Fallback background while loading")
    tags = ArrayField(models.CharField(max_length=40), default=list, blank=True)
    is_product_photo = models.BooleanField(default=False, editable=False)
    is_placeholder = models.BooleanField(default=False, help_text="Development placeholder, never real")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(is_product_photo=False), name="cms_media_not_product"),
            models.CheckConstraint(
                condition=~models.Q(alt_text="") | models.Q(is_decorative=True), name="cms_media_alt_required"
            ),
            models.CheckConstraint(
                condition=models.Q(focal_x__gte=0, focal_x__lte=1, focal_y__gte=0, focal_y__lte=1),
                name="cms_media_focal_in_unit_range",
            ),
            models.CheckConstraint(
                condition=~models.Q(file="") | ~models.Q(external_url=""), name="cms_media_has_source"
            ),
        ]

    def __str__(self) -> str:
        return self.alt_text or self.file.name

    @property
    def src_url(self) -> str:
        return self.external_url or self.file.url


class SiteSettings(TimeStampedModel):
    """Singleton (pk=1). Env vars seed it on first read only; admins own it afterwards."""

    brand_name = models.CharField(max_length=80)
    legal_name = models.CharField(max_length=160, blank=True)
    tagline = models.CharField(max_length=160, blank=True)
    logo = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    monogram = models.CharField(max_length=4, blank=True)
    theme_key = models.CharField(max_length=20, choices=ThemeKey.choices, default=ThemeKey.HEIRLOOM)
    seller_gstin = models.CharField(max_length=15, blank=True)
    seller_state_code = models.CharField(max_length=2, blank=True)
    registered_address = models.TextField(blank=True)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=20, blank=True)
    social_links = models.JSONField(
        default=dict, blank=True, help_text='{"instagram": "https://…", "youtube": "https://…"}'
    )
    announcement = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"enabled": true, "messages": [{"text": "…", "href": "/…"}], "accent": "burgundy"}',
    )
    footer = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"columns": [{"title": "…", "links": [{"label": "…", "href": "/…"}]}], "note": "…"}',
    )
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "site settings"
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="site_settings_singleton")]

    def __str__(self) -> str:
        return f"Site settings · {self.brand_name}"

    def save(self, *args, **kwargs):
        self.pk = 1
        if self.created_at is None:  # a fresh instance replacing the existing row keeps its created_at
            existing = SiteSettings.objects.filter(pk=1).values_list("created_at", flat=True).first()
            self.created_at = existing or timezone.now()
        super().save(*args, **kwargs)


class Page(UUIDModel):
    class Template(models.TextChoices):
        HOME = "home", "Homepage"
        LANDING = "landing", "Campaign landing"
        CONTENT = "content", "Content page"

    slug = models.SlugField(max_length=140, unique=True)
    title = models.CharField(max_length=160)
    template = models.CharField(max_length=10, choices=Template.choices, default=Template.CONTENT)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)
    og_image = models.ForeignKey(
        MediaAsset, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.slug


class PageVersion(UUIDModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField(editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    publish_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True, editable=False)
    published_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+", editable=False
    )
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["page", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["page", "version"], name="page_version_unique"),
            models.UniqueConstraint(
                fields=["page"], condition=models.Q(status="published"), name="one_published_version_per_page"
            ),
            models.CheckConstraint(
                condition=~models.Q(status="scheduled") | models.Q(publish_at__isnull=False),
                name="scheduled_version_has_publish_at",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.page.slug} v{self.version} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.version:
            last = PageVersion.objects.filter(page=self.page).aggregate(m=models.Max("version"))["m"]
            self.version = (last or 0) + 1
        super().save(*args, **kwargs)


class ContentBlock(UUIDModel):
    class Type(models.TextChoices):
        HERO = "hero", "Campaign hero"
        CATEGORY_GRID = "category_grid", "Category mosaic"
        COLLECTION_FEATURE = "collection_feature", "Collection feature"
        PRODUCT_RAIL = "product_rail", "Product rail"
        OCCASION_TILES = "occasion_tiles", "Occasion tiles"
        EDITORIAL_SPLIT = "editorial_split", "Editorial split"
        CRAFT_STORY = "craft_story", "Craft story"
        TESTIMONIALS = "testimonials", "Testimonials"
        INSTAGRAM_GALLERY = "instagram_gallery", "Instagram gallery"
        NEWSLETTER = "newsletter", "Newsletter signup"
        RICH_TEXT = "rich_text", "Rich text"

    page_version = models.ForeignKey(PageVersion, on_delete=models.CASCADE, related_name="blocks")
    type = models.CharField(max_length=20, choices=Type.choices)
    position = models.PositiveIntegerField(default=0)
    config = models.JSONField(default=dict, help_text="Validated against the block's schema (cms/blocks.py)")
    visible_from = models.DateTimeField(null=True, blank=True)
    visible_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["page_version", "position", "created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(visible_until__isnull=True)
                | models.Q(visible_from__isnull=True)
                | models.Q(visible_until__gt=models.F("visible_from")),
                name="block_visibility_window_valid",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_type_display()} #{self.position}"

    def clean(self) -> None:
        from .blocks import BlockConfigError, validate_config

        try:
            self.config = validate_config(self.type, self.config)
        except BlockConfigError as exc:
            raise ValidationError({"config": exc.flat()}) from exc


class Testimonial(UUIDModel):
    """Real customers only, with recorded consent. Dev seed rows are flagged is_placeholder."""

    name = models.CharField(max_length=80)
    quote = models.TextField(max_length=600)
    occasion = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=80, blank=True)
    media = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    consent_recorded_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    is_placeholder = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(is_published=False)
                | models.Q(is_placeholder=True)
                | models.Q(consent_recorded_at__isnull=False),
                name="testimonial_published_needs_consent",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name}: {self.quote[:40]}"


class NewsletterSubscriber(UUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"

    email = models.EmailField(unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    source = models.CharField(max_length=40, blank=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email


class NavigationFeature(UUIDModel):
    """Editorial tile shown in the mega-menu panel of a top-level category."""

    category_path = models.CharField(max_length=500, help_text="Top-level category path, e.g. 'sherwanis'")
    eyebrow = models.CharField(max_length=60, blank=True)
    title = models.CharField(max_length=80)
    href = models.CharField(max_length=300, help_text="Site path starting with '/'")
    media = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, related_name="+")
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category_path", "position"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(href__startswith="/") & ~models.Q(href__startswith="//"),
                name="nav_feature_href_is_site_path",
            )
        ]

    def __str__(self) -> str:
        return f"{self.category_path}: {self.title}"
