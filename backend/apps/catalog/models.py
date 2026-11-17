from django.contrib.postgres.indexes import GinIndex, OpClass
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models

from apps.categories.models import SeoFields
from common.models import SlugNamedModel, UUIDModel

MIN_IMAGE_WIDTH = 1600


class Brand(SlugNamedModel):
    description = models.TextField(blank=True)


class MeasurementDefinition(UUIDModel):
    """Shared measurement vocabulary.

    Body guidance (how to measure) lives here; garment values live in SizeChartRow.
    """

    class AppliesTo(models.TextChoices):
        BODY = "body", "Body"
        GARMENT = "garment", "Garment"
        BOTH = "both", "Body and garment"

    key = models.SlugField(max_length=40, unique=True)
    label = models.CharField(max_length=80)
    applies_to = models.CharField(max_length=10, choices=AppliesTo.choices, default=AppliesTo.BOTH)
    min_cm = models.DecimalField(max_digits=5, decimal_places=1)
    max_cm = models.DecimalField(max_digits=5, decimal_places=1)
    guide_text = models.TextField(blank=True, help_text="How to take this body measurement")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "label"]
        constraints = [
            models.CheckConstraint(condition=models.Q(max_cm__gt=models.F("min_cm")), name="measure_range")
        ]

    def __str__(self) -> str:
        return self.label


class SizeChart(UUIDModel):
    """Garment measurements per size (not body measurements)."""

    name = models.CharField(max_length=120)
    size_system = models.ForeignKey("attributes.SizeSystem", on_delete=models.PROTECT)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class SizeChartRow(models.Model):
    size_chart = models.ForeignKey(SizeChart, on_delete=models.CASCADE, related_name="rows")
    size = models.ForeignKey("attributes.Size", on_delete=models.PROTECT)
    measurement = models.ForeignKey(MeasurementDefinition, on_delete=models.PROTECT)
    value_cm = models.DecimalField(max_digits=5, decimal_places=1)

    class Meta:
        ordering = ["size__sort_order", "measurement__position"]
        constraints = [
            models.UniqueConstraint(
                fields=["size_chart", "size", "measurement"], name="sizechart_cell_unique"
            ),
            models.CheckConstraint(condition=models.Q(value_cm__gt=0), name="sizechart_value_positive"),
        ]

    def __str__(self) -> str:
        return f"{self.size_chart} · {self.size} · {self.measurement}"


class Product(UUIDModel, SeoFields):
    """A garment as merchandised. Never purchasable directly — customers buy a ProductVariant."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class Fulfilment(models.TextChoices):
        READY_TO_WEAR = "ready_to_wear", "Ready to wear"
        MADE_TO_MEASURE = "made_to_measure", "Made to measure"
        BOTH = "both", "Ready to wear and made to measure"

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey("categories.Category", on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.PROTECT, related_name="products")
    fabric = models.ForeignKey("attributes.Fabric", null=True, blank=True, on_delete=models.PROTECT)
    pattern = models.ForeignKey("attributes.Pattern", null=True, blank=True, on_delete=models.PROTECT)
    embroidery = models.ForeignKey(
        "attributes.EmbroideryType", null=True, blank=True, on_delete=models.PROTECT
    )
    sleeve_type = models.ForeignKey("attributes.SleeveType", null=True, blank=True, on_delete=models.PROTECT)
    fit = models.ForeignKey("attributes.Fit", null=True, blank=True, on_delete=models.PROTECT)
    occasions = models.ManyToManyField("attributes.Occasion", blank=True, related_name="products")
    collections = models.ManyToManyField(
        "categories.Collection", through="CollectionProduct", blank=True, related_name="products"
    )
    care_instructions = models.TextField(blank=True)
    fulfilment_type = models.CharField(
        max_length=20, choices=Fulfilment.choices, default=Fulfilment.READY_TO_WEAR
    )
    mtm_lead_time_days = models.PositiveSmallIntegerField(null=True, blank=True)
    size_chart = models.ForeignKey(SizeChart, null=True, blank=True, on_delete=models.SET_NULL)
    hsn_code = models.CharField(max_length=8, help_text="HSN code for GST invoices")
    tax_class = models.ForeignKey("pricing.TaxClass", on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    merch_rank = models.PositiveIntegerField(default=1000, help_text="Lower ranks first in 'Featured' sort")
    is_returnable = models.BooleanField(default=True)
    return_window_days = models.PositiveSmallIntegerField(default=7)
    search_vector = SearchVectorField(null=True, editable=False)

    class Meta:
        ordering = ["merch_rank", "-published_at"]
        indexes = [
            GinIndex(fields=["search_vector"], name="product_search_gin"),
            GinIndex(OpClass("name", name="gin_trgm_ops"), name="product_name_trgm"),
            models.Index(fields=["status", "category"], name="product_status_category"),
            models.Index(fields=["status", "merch_rank", "published_at"], name="product_featured"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(status="published") | models.Q(published_at__isnull=False),
                name="product_published_has_date",
            ),
            models.CheckConstraint(
                condition=models.Q(fulfilment_type="ready_to_wear")
                | models.Q(mtm_lead_time_days__isnull=False),
                name="product_mtm_requires_lead_time",
            ),
            models.CheckConstraint(
                condition=models.Q(hsn_code__regex=r"^[0-9]{4,8}$"), name="product_hsn_format"
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def offers_mtm(self) -> bool:
        return self.fulfilment_type in (self.Fulfilment.MADE_TO_MEASURE, self.Fulfilment.BOTH)

    def clean(self) -> None:
        if self.offers_mtm and not self.mtm_lead_time_days:
            raise ValidationError({"mtm_lead_time_days": "Required for made-to-measure products."})


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specifications")
    key = models.CharField(max_length=60)
    value = models.CharField(max_length=240)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]

    def __str__(self) -> str:
        return f"{self.key}: {self.value}"


def product_media_path(instance: ProductMedia, filename: str) -> str:
    return f"products/{instance.product_id}/{filename}"


class ProductMedia(UUIDModel):
    """Product photography/video (in dev: placeholders or hotlinked demo stock, both flagged
    `is_placeholder`). Campaign imagery belongs to the CMS media library."""

    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    class Role(models.TextChoices):
        PRIMARY = "primary", "Primary"
        GALLERY = "gallery", "Gallery"
        DETAIL = "detail", "Fabric / embroidery detail"
        LIFESTYLE = "lifestyle", "On-model lifestyle"
        SWATCH = "swatch", "Colour swatch"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    colour = models.ForeignKey(
        "attributes.Colour",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        help_text="Shown for variants of this colour; empty = all colours",
    )
    kind = models.CharField(max_length=5, choices=Kind.choices, default=Kind.IMAGE)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.GALLERY)
    file = models.FileField(upload_to=product_media_path, max_length=300, blank=True)
    external_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Hotlinked image (e.g. Unsplash demo stock). Takes precedence over the uploaded file.",
    )
    poster = models.FileField(
        upload_to=product_media_path, max_length=300, blank=True, help_text="Video poster"
    )
    alt_text = models.CharField(max_length=200)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    focal_x = models.FloatField(default=0.5)
    focal_y = models.FloatField(default=0.5)
    position = models.PositiveIntegerField(default=0)
    credit = models.CharField(max_length=120, blank=True, help_text="Photographer, for licensed stock")
    credit_url = models.URLField(max_length=300, blank=True)
    is_placeholder = models.BooleanField(
        default=False, help_text="Development placeholder, never real inventory"
    )

    class Meta:
        ordering = ["position", "created_at"]
        verbose_name_plural = "product media"
        constraints = [
            models.CheckConstraint(condition=~models.Q(alt_text=""), name="media_alt_required"),
            models.CheckConstraint(
                condition=models.Q(focal_x__gte=0, focal_x__lte=1, focal_y__gte=0, focal_y__lte=1),
                name="media_focal_in_unit_range",
            ),
            models.CheckConstraint(
                condition=~models.Q(file="") | ~models.Q(external_url=""), name="media_has_source"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product} · {self.role} #{self.position}"

    @property
    def src_url(self) -> str:
        return self.external_url or self.file.url


class ProductVariant(UUIDModel):
    """The purchasable unit: product × colour × size (size empty for made-to-measure)."""

    class InventoryPolicy(models.TextChoices):
        TRACK = "track", "Track stock"
        MADE_TO_ORDER = "made_to_order", "Made to order (not stock-tracked)"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    colour = models.ForeignKey("attributes.Colour", on_delete=models.PROTECT, related_name="variants")
    size = models.ForeignKey(
        "attributes.Size", null=True, blank=True, on_delete=models.PROTECT, related_name="variants"
    )
    mrp_paise = models.BigIntegerField(help_text="Maximum retail price, GST inclusive")
    sale_price_paise = models.BigIntegerField(
        null=True, blank=True, help_text="Discounted price, GST inclusive"
    )
    inventory_policy = models.CharField(
        max_length=14, choices=InventoryPolicy.choices, default=InventoryPolicy.TRACK
    )
    is_active = models.BooleanField(default=True)
    barcode = models.CharField(max_length=64, blank=True)
    weight_grams = models.PositiveIntegerField(default=1000)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "size__sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "colour", "size"], nulls_distinct=False, name="variant_unique_combo"
            ),
            models.CheckConstraint(condition=models.Q(mrp_paise__gt=0), name="variant_mrp_positive"),
            models.CheckConstraint(
                condition=models.Q(sale_price_paise__isnull=True)
                | models.Q(sale_price_paise__gt=0, sale_price_paise__lt=models.F("mrp_paise")),
                name="variant_sale_below_mrp",
            ),
            models.CheckConstraint(
                condition=models.Q(inventory_policy="made_to_order") | models.Q(size__isnull=False),
                name="variant_tracked_requires_size",
            ),
        ]
        indexes = [models.Index(fields=["product", "is_active"])]

    def __str__(self) -> str:
        return f"{self.sku}"

    @property
    def price_paise(self) -> int:
        return self.sale_price_paise if self.sale_price_paise is not None else self.mrp_paise

    @property
    def label(self) -> str:
        return f"{self.colour.name} / {self.size.label if self.size_id else 'Made to measure'}"


class CollectionProduct(models.Model):
    collection = models.ForeignKey(
        "categories.Collection", on_delete=models.CASCADE, related_name="placements"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="placements")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["collection", "product"], name="collection_product_unique")
        ]

    def __str__(self) -> str:
        return f"{self.collection_id} → {self.product_id}"


class CompleteTheLook(models.Model):
    class Kind(models.TextChoices):
        COMPLETE_LOOK = "complete_look", "Complete the look"
        RELATED = "related", "Related"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="look_links")
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="+")
    kind = models.CharField(max_length=14, choices=Kind.choices, default=Kind.COMPLETE_LOOK)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]
        verbose_name = "Look link"
        constraints = [
            models.UniqueConstraint(fields=["product", "related_product", "kind"], name="look_link_unique"),
            models.CheckConstraint(
                condition=~models.Q(product=models.F("related_product")), name="look_link_not_self"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_id} → {self.related_product_id} ({self.kind})"
