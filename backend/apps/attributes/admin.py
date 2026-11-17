from django.contrib import admin

from . import models


class NamedAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


for m in (
    models.Fabric,
    models.Fit,
    models.Pattern,
    models.EmbroideryType,
    models.SleeveType,
    models.SizeSystem,
):
    admin.site.register(m, NamedAdmin)


@admin.register(models.Occasion)
class OccasionAdmin(NamedAdmin):
    list_display = ["name", "slug", "position"]


@admin.register(models.Colour)
class ColourAdmin(NamedAdmin):
    list_display = ["name", "hex", "family"]
    list_filter = ["family"]


@admin.register(models.Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ["label", "system", "sort_order"]
    list_filter = ["system"]
    search_fields = ["label"]
