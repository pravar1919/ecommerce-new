from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import Category, Collection


def active_categories() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True).order_by("depth", "position", "name")


def category_by_path(path: str) -> Category | None:
    return active_categories().filter(path=path.strip("/")).first()


def category_subtree_paths(path: str) -> Q:
    """Q matching a category and all its descendants on a `category__path` lookup."""
    path = path.strip("/")
    return Q(category__path=path) | Q(category__path__startswith=f"{path}/")


def live_collections() -> QuerySet[Collection]:
    now = timezone.now()
    return Collection.objects.filter(is_published=True).filter(
        Q(starts_at__isnull=True) | Q(starts_at__lte=now), Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    )
