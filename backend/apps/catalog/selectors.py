"""Read-side queries for the storefront catalogue: listing, filters, facets, search, detail.

Stock is read through the `stock_levels` reverse relation (owned by the inventory app) without
importing inventory code, keeping catalog independent of commerce apps.
"""

from dataclasses import dataclass, field

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramWordSimilarity
from django.db.models import (
    Count,
    Exists,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from apps.attributes.models import Colour, EmbroideryType, Fabric, Fit, Occasion, Pattern, Size
from apps.categories.selectors import category_subtree_paths

from .models import CompleteTheLook, Product, ProductMedia, ProductVariant
from .services import SEARCH_CONFIG

TRIGRAM_THRESHOLD = 0.3

ORDERINGS = {
    "featured": ["merch_rank", "-published_at"],
    "newest": ["-published_at"],
    "price_asc": ["price_from", "merch_rank"],
    "price_desc": ["-price_from", "merch_rank"],
    # "bestselling" falls back to featured until order analytics exist (Phase 6).
    "bestselling": ["merch_rank", "-published_at"],
}


@dataclass
class ProductFilters:
    q: str = ""
    category: str = ""
    collection: str = ""
    occasion: list[str] = field(default_factory=list)
    colour: list[str] = field(default_factory=list)
    size: list[str] = field(default_factory=list)
    fabric: list[str] = field(default_factory=list)
    fit: list[str] = field(default_factory=list)
    embroidery: list[str] = field(default_factory=list)
    pattern: list[str] = field(default_factory=list)
    fulfilment: str = ""
    price_min: int | None = None
    price_max: int | None = None
    in_stock: bool = False
    ordering: str = "featured"


_effective_price = Coalesce("sale_price_paise", "mrp_paise")


def _variant_available_q() -> Q:
    return Q(inventory_policy=ProductVariant.InventoryPolicy.MADE_TO_ORDER) | Q(
        stock_levels__on_hand__gt=F("stock_levels__reserved")
    )


def published_products() -> QuerySet[Product]:
    active_variants = ProductVariant.objects.filter(product=OuterRef("pk"), is_active=True)
    priced = active_variants.annotate(p=_effective_price)
    return (
        Product.objects.filter(status=Product.Status.PUBLISHED, category__is_active=True)
        .filter(Exists(active_variants))
        .annotate(
            price_from=Subquery(priced.order_by("p").values("p")[:1], output_field=IntegerField()),
            price_to=Subquery(priced.order_by("-p").values("p")[:1], output_field=IntegerField()),
            mrp_from=Subquery(priced.order_by("p").values("mrp_paise")[:1], output_field=IntegerField()),
            has_sale=Exists(active_variants.filter(sale_price_paise__isnull=False)),
            in_stock=Exists(active_variants.filter(_variant_available_q())),
        )
    )


def apply_filters(qs: QuerySet[Product], f: ProductFilters, *, skip: str | None = None) -> QuerySet[Product]:
    """Apply all filters except `skip` (used for disjunctive facet counts)."""
    if f.q:
        query = SearchQuery(f.q, search_type="websearch", config=SEARCH_CONFIG)
        qs = qs.annotate(
            rank=SearchRank(F("search_vector"), query), sim=TrigramWordSimilarity(f.q, "name")
        ).filter(Q(search_vector=query) | Q(sim__gte=TRIGRAM_THRESHOLD))
    if f.category and skip != "category":
        qs = qs.filter(category_subtree_paths(f.category))
    if f.collection:
        qs = qs.filter(placements__collection__slug=f.collection, placements__collection__is_published=True)
    if f.occasion and skip != "occasion":
        qs = qs.filter(
            Exists(
                Product.occasions.through.objects.filter(
                    product_id=OuterRef("pk"), occasion__slug__in=f.occasion
                )
            )
        )
    for name in ("fabric", "fit", "embroidery", "pattern"):
        values = getattr(f, name)
        if values and skip != name:
            qs = qs.filter(**{f"{name}__slug__in": values})
    if f.fulfilment and skip != "fulfilment":
        if f.fulfilment == "made_to_measure":
            qs = qs.filter(fulfilment_type__in=[Product.Fulfilment.MADE_TO_MEASURE, Product.Fulfilment.BOTH])
        elif f.fulfilment == "ready_to_wear":
            qs = qs.filter(fulfilment_type__in=[Product.Fulfilment.READY_TO_WEAR, Product.Fulfilment.BOTH])

    # Variant-level conditions must hold on the *same* variant (e.g. ivory AND size 40 AND in stock).
    vq = Q()
    if f.colour and skip != "colour":
        vq &= Q(colour__slug__in=f.colour)
    if f.size and skip != "size":
        vq &= Q(size__label__in=f.size)
    if f.in_stock:
        vq &= _variant_available_q()
    price_bounds = skip != "price" and (f.price_min is not None or f.price_max is not None)
    if vq or price_bounds:
        variants = ProductVariant.objects.filter(product=OuterRef("pk"), is_active=True).annotate(
            p=_effective_price
        )
        if f.price_min is not None and skip != "price":
            variants = variants.filter(p__gte=f.price_min)
        if f.price_max is not None and skip != "price":
            variants = variants.filter(p__lte=f.price_max)
        qs = qs.filter(Exists(variants.filter(vq)))
    return qs


def _listing_prefetch(qs: QuerySet[Product]) -> QuerySet[Product]:
    return qs.select_related("category").prefetch_related(
        Prefetch(
            "media", queryset=ProductMedia.objects.filter(kind="image").order_by("position", "created_at")
        ),
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.filter(is_active=True)
            .select_related("colour")
            .order_by("position"),
            to_attr="active_variants",
        ),
    )


def list_products(f: ProductFilters) -> QuerySet[Product]:
    qs = apply_filters(published_products(), f)
    if f.q and f.ordering in ("", "featured", "relevance"):
        qs = qs.order_by(F("rank").desc(nulls_last=True), F("sim").desc(), "merch_rank")
    else:
        qs = qs.order_by(*ORDERINGS.get(f.ordering, ORDERINGS["featured"]), "pk")
    return _listing_prefetch(qs.distinct() if f.collection else qs)


def products_by_ids(ids) -> QuerySet[Product]:
    """Published products for curated lists (CMS rails). Caller restores the curated order."""
    return _listing_prefetch(published_products().filter(pk__in=list(ids)))


def _ids(f: ProductFilters, skip: str) -> QuerySet:
    return apply_filters(published_products(), f, skip=skip).values("pk")


def product_facets(f: ProductFilters) -> dict:
    """Disjunctive facets: each facet's counts ignore that facet's own selection."""

    def lookup_facet(model, relation: str, skip: str, extra: Q | None = None):
        ids = _ids(f, skip)
        rows = (
            model.objects.filter(Q(**{f"{relation}__in": ids}) & (extra or Q()))
            .annotate(count=Count(relation, distinct=True))
            .filter(count__gt=0)
        )
        return rows

    colour_rows = lookup_facet(Colour, "variants__product", "colour", Q(variants__is_active=True))
    size_rows = lookup_facet(Size, "variants__product", "size", Q(variants__is_active=True)).select_related(
        "system"
    )
    occasion_rows = lookup_facet(Occasion, "products", "occasion")
    simple = {}
    for name, model in (
        ("fabric", Fabric),
        ("fit", Fit),
        ("embroidery", EmbroideryType),
        ("pattern", Pattern),
    ):
        simple[name] = [
            {"slug": r.slug, "name": r.name, "count": r.count}
            for r in model.objects.filter(product__in=_ids(f, name))
            .annotate(count=Count("product", distinct=True))
            .order_by("name")
        ]
    price = apply_filters(published_products(), f, skip="price").aggregate(
        min=Min("price_from"), max=Max("price_from")
    )
    fulfil_ids = apply_filters(published_products(), f, skip="fulfilment")
    return {
        "colour": [
            {"slug": c.slug, "name": c.name, "hex": c.hex, "family": c.family, "count": c.count}
            for c in colour_rows.order_by("family", "name")
        ],
        "size": [
            {"label": s.label, "system": s.system.name, "count": s.count}
            for s in size_rows.order_by("system__name", "sort_order")
        ],
        "occasion": [
            {"slug": o.slug, "name": o.name, "count": o.count} for o in occasion_rows.order_by("position")
        ],
        **simple,
        "fulfilment": [
            {
                "value": "ready_to_wear",
                "count": fulfil_ids.exclude(fulfilment_type="made_to_measure").count(),
            },
            {
                "value": "made_to_measure",
                "count": fulfil_ids.exclude(fulfilment_type="ready_to_wear").count(),
            },
        ],
        "price": {"min": price["min"], "max": price["max"]},
    }


def search_suggestions(q: str, *, limit: int = 6) -> dict:
    from apps.categories.models import Category

    q = q.strip()
    if len(q) < 2:
        return {"products": [], "categories": [], "queries": []}
    products = list(list_products(ProductFilters(q=q, ordering="relevance"))[:limit])
    categories = list(
        Category.objects.filter(is_active=True)
        .annotate(sim=TrigramWordSimilarity(q, "name"))
        .filter(Q(sim__gte=TRIGRAM_THRESHOLD) | Q(name__icontains=q))
        .order_by("-sim")[:4]
    )
    queries: list[str] = []
    for model in (EmbroideryType, Fabric, Occasion):
        queries += list(
            model.objects.annotate(sim=TrigramWordSimilarity(q, "name"))
            .filter(Q(sim__gte=TRIGRAM_THRESHOLD) | Q(name__icontains=q))
            .order_by("-sim")
            .values_list("name", flat=True)[:2]
        )
    return {"products": products, "categories": categories, "queries": queries[:5]}


def variants_with_stock(product: Product) -> QuerySet[ProductVariant]:
    return (
        product.variants.filter(is_active=True)
        .select_related("colour", "size")
        .annotate(
            on_hand=Coalesce(Sum("stock_levels__on_hand"), Value(0)),
            reserved=Coalesce(Sum("stock_levels__reserved"), Value(0)),
        )
        .order_by("colour__name", "size__sort_order")
    )


def stock_status(variant: ProductVariant) -> tuple[str, int | None]:
    if variant.inventory_policy == ProductVariant.InventoryPolicy.MADE_TO_ORDER:
        return "made_to_order", None
    available = max(variant.on_hand - variant.reserved, 0)
    if available == 0:
        return "out_of_stock", None
    if available <= settings.LOW_STOCK_DISPLAY_THRESHOLD:
        return "low_stock", available
    return "in_stock", None


def product_detail(slug: str) -> Product | None:
    return (
        published_products()
        .select_related(
            "category",
            "brand",
            "fabric",
            "pattern",
            "embroidery",
            "sleeve_type",
            "fit",
            "size_chart__size_system",
        )
        .prefetch_related(
            "occasions",
            "specifications",
            Prefetch("media", queryset=ProductMedia.objects.select_related("colour").order_by("position")),
        )
        .filter(slug=slug)
        .first()
    )


def related_products(product: Product, *, limit: int = 8) -> QuerySet[Product]:
    curated = CompleteTheLook.objects.filter(product=product, kind=CompleteTheLook.Kind.RELATED).values(
        "related_product"
    )
    qs = (
        published_products()
        .exclude(pk=product.pk)
        .filter(Q(pk__in=curated) | Q(category_id=product.category_id))
    )
    return _listing_prefetch(qs.order_by("merch_rank", "-published_at"))[:limit]


def complete_the_look(product: Product, *, limit: int = 6) -> list[Product]:
    links = list(
        CompleteTheLook.objects.filter(product=product, kind=CompleteTheLook.Kind.COMPLETE_LOOK)
        .order_by("position")
        .values_list("related_product_id", flat=True)[:limit]
    )
    by_id = {p.pk: p for p in _listing_prefetch(published_products().filter(pk__in=links))}
    return [by_id[i] for i in links if i in by_id]
