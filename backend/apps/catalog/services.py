from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models import TextField, Value
from django.utils import timezone

from common.exceptions import InvalidOperation

from .models import Product

SEARCH_CONFIG = "english"


def _doc(*parts: str | None) -> Value:
    return Value(" ".join(p for p in parts if p), output_field=TextField())


def update_search_vectors(product_ids) -> int:
    """Rebuild weighted FTS vectors.

    A = name; B = category, fabric, embroidery, occasions, colours; C = descriptions.
    """
    qs = (
        Product.objects.filter(pk__in=list(product_ids))
        .select_related("category", "fabric", "embroidery", "pattern", "fit", "brand")
        .prefetch_related("occasions", "variants__colour")
    )
    count = 0
    for p in qs:
        colours = {v.colour.name for v in p.variants.all()}
        b = _doc(
            p.category.name,
            p.fabric and p.fabric.name,
            p.embroidery and p.embroidery.name,
            p.pattern and p.pattern.name,
            p.fit and p.fit.name,
            p.brand and p.brand.name,
            *[o.name for o in p.occasions.all()],
            *colours,
        )
        vector = (
            SearchVector(_doc(p.name), weight="A", config=SEARCH_CONFIG)
            + SearchVector(b, weight="B", config=SEARCH_CONFIG)
            + SearchVector(_doc(p.short_description, p.description), weight="C", config=SEARCH_CONFIG)
        )
        Product.objects.filter(pk=p.pk).update(search_vector=vector)
        count += 1
    return count


@transaction.atomic
def publish_product(product: Product) -> Product:
    product = Product.objects.select_for_update().get(pk=product.pk)
    if not product.variants.filter(is_active=True).exists():
        raise InvalidOperation("A product needs at least one active variant before publishing.")
    if not product.media.filter(kind="image").exists():
        raise InvalidOperation("A product needs at least one image before publishing.")
    product.status = Product.Status.PUBLISHED
    product.published_at = product.published_at or timezone.now()
    product.save(update_fields=["status", "published_at", "updated_at"])
    transaction.on_commit(lambda: update_search_vectors([product.pk]))
    return product


@transaction.atomic
def archive_product(product: Product) -> Product:
    Product.objects.filter(pk=product.pk).update(status=Product.Status.ARCHIVED, updated_at=timezone.now())
    product.refresh_from_db()
    return product
