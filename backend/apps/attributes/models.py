"""First-class product facets as typed lookup tables (integrity + fast filtering + admin dropdowns)."""

from django.db import models

from common.models import SlugNamedModel, UUIDModel


class Fabric(SlugNamedModel):
    composition = models.CharField(max_length=160, blank=True, help_text="e.g. 70% silk, 30% viscose")
    description = models.TextField(blank=True)


class Occasion(SlugNamedModel):
    position = models.PositiveIntegerField(default=0)

    class Meta(SlugNamedModel.Meta):
        ordering = ["position", "name"]


class Fit(SlugNamedModel):
    pass


class Pattern(SlugNamedModel):
    pass


class EmbroideryType(SlugNamedModel):
    description = models.TextField(blank=True)


class SleeveType(SlugNamedModel):
    pass


class Colour(SlugNamedModel):
    hex = models.CharField(max_length=7, help_text="#RRGGBB")
    family = models.CharField(max_length=40, help_text="Filter grouping, e.g. 'red', 'neutral'")

    class Meta(SlugNamedModel.Meta):
        constraints = [
            models.CheckConstraint(condition=models.Q(hex__regex=r"^#[0-9A-F]{6}$"), name="colour_hex_upper")
        ]

    def save(self, *args, **kwargs):
        self.hex = self.hex.upper()
        super().save(*args, **kwargs)


class SizeSystem(SlugNamedModel):
    """e.g. 'Menswear chest (in)', 'Trouser waist', 'Footwear UK'."""


class Size(UUIDModel):
    system = models.ForeignKey(SizeSystem, on_delete=models.PROTECT, related_name="sizes")
    label = models.CharField(max_length=20)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["system", "sort_order"]
        constraints = [models.UniqueConstraint(fields=["system", "label"], name="size_unique_per_system")]

    def __str__(self) -> str:
        return self.label
