from django.contrib import admin

from .models import Category, Collection


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["path", "name", "position", "is_active"]
    list_filter = ["is_active", "depth"]
    search_fields = ["name", "slug", "path"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ["path", "depth"]
    autocomplete_fields = ["parent"]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "kind", "accent", "is_published", "starts_at", "ends_at", "position"]
    list_filter = ["is_published", "kind", "accent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
