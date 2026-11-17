from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.categories.models import Category, Collection
from common.money import money_dict

from .. import selectors
from ..models import MeasurementDefinition, Product, ProductMedia, ProductVariant, SizeChart

NEW_ARRIVAL_DAYS = 30


# ---------- query params ----------------------------------------------------------------
class CommaList(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return [v.strip() for v in value.split(",") if v.strip()][:20]


class ProductQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=100)
    category = serializers.CharField(required=False, allow_blank=True, max_length=300)
    collection = serializers.SlugField(required=False, allow_blank=True)
    occasion = CommaList(required=False)
    colour = CommaList(required=False)
    size = CommaList(required=False)
    fabric = CommaList(required=False)
    fit = CommaList(required=False)
    embroidery = CommaList(required=False)
    pattern = CommaList(required=False)
    fulfilment = serializers.ChoiceField(choices=["ready_to_wear", "made_to_measure"], required=False)
    price_min = serializers.IntegerField(required=False, min_value=0, help_text="paise")
    price_max = serializers.IntegerField(required=False, min_value=0, help_text="paise")
    in_stock = serializers.BooleanField(required=False, default=False)
    ordering = serializers.ChoiceField(
        choices=["featured", "newest", "price_asc", "price_desc", "bestselling", "relevance"],
        required=False,
        default="featured",
    )

    def validate(self, attrs):
        lo, hi = attrs.get("price_min"), attrs.get("price_max")
        if lo is not None and hi is not None and lo > hi:
            raise serializers.ValidationError({"price_max": "Must be greater than or equal to price_min."})
        return attrs

    def to_filters(self) -> selectors.ProductFilters:
        return selectors.ProductFilters(**self.validated_data)


# ---------- shared shapes -----------------------------------------------------------------
class MoneySerializer(serializers.Serializer):
    amount = serializers.IntegerField(help_text="paise")
    currency = serializers.CharField()
    formatted = serializers.CharField()


class ImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    alt = serializers.CharField(source="alt_text")

    class Meta:
        model = ProductMedia
        fields = ["id", "url", "alt", "width", "height", "focal_x", "focal_y", "is_placeholder"]

    def get_url(self, obj) -> str:
        return obj.file.url


class MediaSerializer(ImageSerializer):
    colour = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    poster_url = serializers.SerializerMethodField()

    class Meta(ImageSerializer.Meta):
        fields = [*ImageSerializer.Meta.fields, "kind", "role", "colour", "poster_url"]

    def get_poster_url(self, obj) -> str | None:
        return obj.poster.url if obj.poster else None


class CategoryRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "path"]


class PriceSerializer(serializers.Serializer):
    current = MoneySerializer(help_text="Lowest current price across active variants")
    mrp = MoneySerializer(help_text="MRP of the lowest-priced variant")
    has_range = serializers.BooleanField()
    on_sale = serializers.BooleanField()
    discount_percent = serializers.IntegerField(allow_null=True)


def price_block(current: int, mrp: int, to: int | None) -> dict:
    on_sale = current < mrp
    return {
        "current": money_dict(current),
        "mrp": money_dict(mrp),
        "has_range": bool(to and to != current),
        "on_sale": on_sale,
        "discount_percent": round((mrp - current) * 100 / mrp) if on_sale else None,
    }


class ColourOptionSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    hex = serializers.CharField()
    image = ImageSerializer(allow_null=True)


# ---------- listing ---------------------------------------------------------------------------
class ProductCardSerializer(serializers.ModelSerializer):
    category = CategoryRefSerializer()
    price = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    hover_image = serializers.SerializerMethodField()
    colours = serializers.SerializerMethodField()
    is_mtm_available = serializers.BooleanField(source="offers_mtm")
    in_stock = serializers.BooleanField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "category",
            "price",
            "badges",
            "primary_image",
            "hover_image",
            "colours",
            "is_mtm_available",
            "in_stock",
        ]

    def _images(self, obj) -> list[ProductMedia]:
        imgs = list(obj.media.all())
        primary = [m for m in imgs if m.role == ProductMedia.Role.PRIMARY]
        return primary[:1] + [m for m in imgs if m not in primary[:1]]

    @extend_schema_field(PriceSerializer)
    def get_price(self, obj):
        return price_block(obj.price_from, obj.mrp_from, obj.price_to)

    def get_badges(self, obj) -> list[str]:
        badges = []
        if obj.published_at and obj.published_at >= timezone.now() - timedelta(days=NEW_ARRIVAL_DAYS):
            badges.append("new")
        if obj.has_sale:
            badges.append("sale")
        if obj.offers_mtm:
            badges.append("made_to_measure")
        if not obj.in_stock:
            badges.append("sold_out")
        return badges

    @extend_schema_field(ImageSerializer(allow_null=True))
    def get_primary_image(self, obj):
        imgs = self._images(obj)
        return ImageSerializer(imgs[0]).data if imgs else None

    @extend_schema_field(ImageSerializer(allow_null=True))
    def get_hover_image(self, obj):
        imgs = self._images(obj)
        return ImageSerializer(imgs[1]).data if len(imgs) > 1 else None

    @extend_schema_field(ColourOptionSerializer(many=True))
    def get_colours(self, obj):
        seen, out = set(), []
        imgs = list(obj.media.all())
        for v in getattr(obj, "active_variants", []):
            if v.colour_id in seen:
                continue
            seen.add(v.colour_id)
            img = next((m for m in imgs if m.colour_id == v.colour_id), None)
            out.append(
                {
                    "slug": v.colour.slug,
                    "name": v.colour.name,
                    "hex": v.colour.hex,
                    "image": ImageSerializer(img).data if img else None,
                }
            )
        return out


# ---------- facets ----------------------------------------------------------------------------
class FacetValueSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class ColourFacetSerializer(FacetValueSerializer):
    hex = serializers.CharField()
    family = serializers.CharField()


class SizeFacetSerializer(serializers.Serializer):
    label = serializers.CharField()
    system = serializers.CharField()
    count = serializers.IntegerField()


class FulfilmentFacetSerializer(serializers.Serializer):
    value = serializers.CharField()
    count = serializers.IntegerField()


class PriceRangeSerializer(serializers.Serializer):
    min = serializers.IntegerField(allow_null=True)
    max = serializers.IntegerField(allow_null=True)


class FacetsSerializer(serializers.Serializer):
    colour = ColourFacetSerializer(many=True)
    size = SizeFacetSerializer(many=True)
    occasion = FacetValueSerializer(many=True)
    fabric = FacetValueSerializer(many=True)
    fit = FacetValueSerializer(many=True)
    embroidery = FacetValueSerializer(many=True)
    pattern = FacetValueSerializer(many=True)
    fulfilment = FulfilmentFacetSerializer(many=True)
    price = PriceRangeSerializer()


# ---------- detail -----------------------------------------------------------------------------
class NamedRefSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()


class VariantSerializer(serializers.ModelSerializer):
    colour = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    size = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    low_stock_quantity = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "colour",
            "size",
            "price",
            "inventory_policy",
            "stock_status",
            "low_stock_quantity",
        ]

    def get_size(self, obj) -> str | None:
        return obj.size.label if obj.size_id else None

    @extend_schema_field(PriceSerializer)
    def get_price(self, obj):
        return price_block(obj.price_paise, obj.mrp_paise, None)

    @extend_schema_field(
        serializers.ChoiceField(choices=["in_stock", "low_stock", "out_of_stock", "made_to_order"])
    )
    def get_stock_status(self, obj):
        return selectors.stock_status(obj)[0]

    def get_low_stock_quantity(self, obj) -> int | None:
        return selectors.stock_status(obj)[1]


class SizeChartCellSerializer(serializers.Serializer):
    measurement = serializers.CharField()
    value_cm = serializers.DecimalField(max_digits=5, decimal_places=1)


class SizeChartRowSerializer(serializers.Serializer):
    size = serializers.CharField()
    measurements = SizeChartCellSerializer(many=True)


class MeasurementDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementDefinition
        fields = ["key", "label", "applies_to", "min_cm", "max_cm", "guide_text"]


class SizeChartSerializer(serializers.ModelSerializer):
    size_system = serializers.CharField(source="size_system.name")
    columns = serializers.SerializerMethodField()
    rows = serializers.SerializerMethodField()

    class Meta:
        model = SizeChart
        fields = ["id", "name", "size_system", "notes", "columns", "rows"]

    def _rows(self, obj):
        return list(obj.rows.select_related("size", "measurement").all())

    @extend_schema_field(MeasurementDefinitionSerializer(many=True))
    def get_columns(self, obj):
        seen, cols = set(), []
        for r in self._rows(obj):
            if r.measurement_id not in seen:
                seen.add(r.measurement_id)
                cols.append(r.measurement)
        return MeasurementDefinitionSerializer(cols, many=True).data

    @extend_schema_field(SizeChartRowSerializer(many=True))
    def get_rows(self, obj):
        grouped: dict[str, list] = {}
        for r in self._rows(obj):
            grouped.setdefault(r.size.label, []).append(
                {"measurement": r.measurement.key, "value_cm": r.value_cm}
            )
        return [{"size": k, "measurements": v} for k, v in grouped.items()]


class SpecificationSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()


class SeoSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()


def _ref(obj):
    return {"slug": obj.slug, "name": obj.name} if obj else None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategoryRefSerializer()
    brand = serializers.SerializerMethodField()
    fabric = serializers.SerializerMethodField()
    pattern = serializers.SerializerMethodField()
    embroidery = serializers.SerializerMethodField()
    sleeve_type = serializers.SerializerMethodField()
    fit = serializers.SerializerMethodField()
    occasions = NamedRefSerializer(many=True)
    price = serializers.SerializerMethodField()
    media = MediaSerializer(many=True)
    variants = serializers.SerializerMethodField()
    specifications = SpecificationSerializer(many=True)
    size_chart = SizeChartSerializer(allow_null=True)
    fabric_composition = serializers.SerializerMethodField()
    is_mtm_available = serializers.BooleanField(source="offers_mtm")
    in_stock = serializers.BooleanField()
    seo = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "short_description",
            "description",
            "category",
            "brand",
            "fabric",
            "fabric_composition",
            "pattern",
            "embroidery",
            "sleeve_type",
            "fit",
            "occasions",
            "care_instructions",
            "fulfilment_type",
            "is_mtm_available",
            "mtm_lead_time_days",
            "is_returnable",
            "return_window_days",
            "price",
            "in_stock",
            "media",
            "variants",
            "specifications",
            "size_chart",
            "seo",
        ]

    @extend_schema_field(NamedRefSerializer(allow_null=True))
    def get_brand(self, obj):
        return _ref(obj.brand)

    @extend_schema_field(NamedRefSerializer(allow_null=True))
    def get_fabric(self, obj):
        return _ref(obj.fabric)

    def get_fabric_composition(self, obj) -> str | None:
        return obj.fabric.composition if obj.fabric else None

    @extend_schema_field(NamedRefSerializer(allow_null=True))
    def get_pattern(self, obj):
        return _ref(obj.pattern)

    @extend_schema_field(NamedRefSerializer(allow_null=True))
    def get_embroidery(self, obj):
        return _ref(obj.embroidery)

    @extend_schema_field(NamedRefSerializer(allow_null=True))
    def get_sleeve_type(self, obj):
        return _ref(obj.sleeve_type)

    @extend_schema_field(NamedRefSerializer(allow_null=True))
    def get_fit(self, obj):
        return _ref(obj.fit)

    @extend_schema_field(PriceSerializer)
    def get_price(self, obj):
        return price_block(obj.price_from, obj.mrp_from, obj.price_to)

    @extend_schema_field(VariantSerializer(many=True))
    def get_variants(self, obj):
        return VariantSerializer(selectors.variants_with_stock(obj), many=True).data

    @extend_schema_field(SeoSerializer)
    def get_seo(self, obj):
        return {
            "title": obj.seo_title or obj.name,
            "description": obj.seo_description or obj.short_description,
        }


# ---------- taxonomy -----------------------------------------------------------------------------
class CategoryNodeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "path", "depth", "children"]

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_children(self, obj):
        kids = self.context.get("children", {}).get(obj.pk, [])
        return CategoryNodeSerializer(kids, many=True, context=self.context).data


class CategoryDetailSerializer(serializers.ModelSerializer):
    breadcrumbs = serializers.SerializerMethodField()
    children = CategoryRefSerializer(many=True, source="active_children")
    seo = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "path", "eyebrow", "description", "breadcrumbs", "children", "seo"]

    @extend_schema_field(CategoryRefSerializer(many=True))
    def get_breadcrumbs(self, obj):
        chain, node = [], obj.parent
        while node is not None:
            chain.insert(0, node)
            node = node.parent
        return CategoryRefSerializer(chain, many=True).data

    @extend_schema_field(SeoSerializer)
    def get_seo(self, obj):
        return {
            "title": obj.seo_title or obj.name,
            "description": obj.seo_description or obj.description[:160],
        }


class CollectionSerializer(serializers.ModelSerializer):
    seo = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ["id", "name", "slug", "eyebrow", "description", "accent", "starts_at", "ends_at", "seo"]

    @extend_schema_field(SeoSerializer)
    def get_seo(self, obj):
        return {
            "title": obj.seo_title or obj.name,
            "description": obj.seo_description or obj.description[:160],
        }


class SuggestCategorySerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()


class SuggestProductSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    price = PriceSerializer()
    image = ImageSerializer(allow_null=True)


class SuggestionsSerializer(serializers.Serializer):
    products = SuggestProductSerializer(many=True)
    categories = SuggestCategorySerializer(many=True)
    queries = serializers.ListField(child=serializers.CharField())
