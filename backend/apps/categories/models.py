from django.core.exceptions import ValidationError
from django.db import models, transaction

from common.models import UUIDModel

MAX_DEPTH = 3


class SeoFields(models.Model):
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)

    class Meta:
        abstract = True


class Category(UUIDModel, SeoFields):
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    path = models.CharField(max_length=500, unique=True, editable=False, help_text="e.g. wedding/sherwanis")
    depth = models.PositiveSmallIntegerField(default=0, editable=False)
    position = models.PositiveIntegerField(default=0)
    eyebrow = models.CharField(max_length=80, blank=True, help_text="Small label above the title")
    description = models.TextField(blank=True, help_text="Editorial intro shown on the category page")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["path"]
        verbose_name_plural = "categories"
        constraints = [
            models.CheckConstraint(condition=models.Q(depth__lte=MAX_DEPTH), name="category_max_depth")
        ]
        indexes = [models.Index(fields=["parent", "position"])]

    def __str__(self) -> str:
        return self.path or self.name

    def save(self, *args, **kwargs):
        old_path = None
        if self.pk:
            old_path = Category.objects.filter(pk=self.pk).values_list("path", flat=True).first()
        self.path, self.depth = self._compute_path()
        with transaction.atomic():
            super().save(*args, **kwargs)
            if old_path and old_path != self.path:
                for child in self.children.all():
                    child.save()  # cascades path updates down the tree

    def clean(self) -> None:
        node = self.parent
        while node is not None:
            if node.pk == self.pk:
                raise ValidationError({"parent": "A category cannot be its own ancestor."})
            node = node.parent

    def _compute_path(self) -> tuple[str, int]:
        if self.parent_id is None:
            return self.slug, 0
        parent = Category.objects.only("path", "depth").get(pk=self.parent_id)
        return f"{parent.path}/{self.slug}", parent.depth + 1


class Collection(UUIDModel, SeoFields):
    class Kind(models.TextChoices):
        MANUAL = "manual", "Manually curated"
        RULE = "rule", "Rule based"

    class Accent(models.TextChoices):
        BURGUNDY = "burgundy", "Burgundy"
        EMERALD = "emerald", "Emerald"
        ROYAL = "royal", "Royal blue"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.MANUAL)
    rules = models.JSONField(default=dict, blank=True, help_text="Filter params for rule-based collections")
    eyebrow = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    accent = models.CharField(max_length=10, choices=Accent.choices, default=Accent.BURGUNDY)
    is_published = models.BooleanField(default=False)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__isnull=True)
                | models.Q(starts_at__isnull=True)
                | models.Q(ends_at__gt=models.F("starts_at")),
                name="collection_window_valid",
            )
        ]

    def __str__(self) -> str:
        return self.name
