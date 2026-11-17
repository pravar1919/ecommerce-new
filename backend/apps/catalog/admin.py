from django.contrib import admin, messages

from common.exceptions import DomainError

from . import services
from .models import (
    Brand,
    CollectionProduct,
    CompleteTheLook,
    MeasurementDefinition,
    Product,
    ProductMedia,
    ProductSpecification,
    ProductVariant,
    SizeChart,
    SizeChartRow,
)


class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = [
        "sku",
        "colour",
        "size",
        "mrp_paise",
        "sale_price_paise",
        "inventory_policy",
        "is_active",
        "position",
    ]
    autocomplete_fields = ["colour", "size"]


class MediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 0
    fields = ["file", "kind", "role", "colour", "alt_text", "width", "height", "position", "is_placeholder"]
    readonly_fields = ["is_placeholder"]


class SpecInline(admin.TabularInline):
    model = ProductSpecification
    extra = 0


class PlacementInline(admin.TabularInline):
    model = CollectionProduct
    extra = 0
    autocomplete_fields = ["collection"]


class LookInline(admin.TabularInline):
    model = CompleteTheLook
    fk_name = "product"
    extra = 0
    autocomplete_fields = ["related_product"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "status", "fulfilment_type", "merch_rank", "published_at"]
    list_filter = ["status", "fulfilment_type", "category", "occasions", "fabric", "embroidery"]
    search_fields = ["name", "slug", "variants__sku"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = [
        "category",
        "brand",
        "fabric",
        "pattern",
        "embroidery",
        "sleeve_type",
        "fit",
        "size_chart",
    ]
    filter_horizontal = ["occasions"]
    readonly_fields = ["status", "published_at"]
    inlines = [VariantInline, MediaInline, SpecInline, PlacementInline, LookInline]
    actions = ["publish", "archive"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "brand", "status", "published_at", "merch_rank")}),
        ("Story", {"fields": ("short_description", "description", "care_instructions")}),
        ("Attributes", {"fields": ("fabric", "pattern", "embroidery", "sleeve_type", "fit", "occasions")}),
        (
            "Fulfilment & sizing",
            {
                "fields": (
                    "fulfilment_type",
                    "mtm_lead_time_days",
                    "size_chart",
                    "is_returnable",
                    "return_window_days",
                )
            },
        ),
        ("Tax", {"fields": ("hsn_code", "tax_class")}),
        ("SEO", {"fields": ("seo_title", "seo_description")}),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        services.update_search_vectors([form.instance.pk])

    @admin.action(description="Publish selected products")
    def publish(self, request, queryset):
        ok = 0
        for product in queryset:
            try:
                services.publish_product(product)
                ok += 1
            except DomainError as exc:
                self.message_user(request, f"{product}: {exc.message}", messages.ERROR)
        if ok:
            self.message_user(request, f"Published {ok} product(s).", messages.SUCCESS)

    @admin.action(description="Archive selected products")
    def archive(self, request, queryset):
        for product in queryset:
            services.archive_product(product)
        self.message_user(request, f"Archived {queryset.count()} product(s).", messages.SUCCESS)


@admin.register(ProductVariant)
class VariantAdmin(admin.ModelAdmin):
    list_display = [
        "sku",
        "product",
        "colour",
        "size",
        "mrp_paise",
        "sale_price_paise",
        "inventory_policy",
        "is_active",
    ]
    list_filter = ["inventory_policy", "is_active", "colour"]
    search_fields = ["sku", "product__name", "barcode"]
    autocomplete_fields = ["product", "colour", "size"]


class SizeChartRowInline(admin.TabularInline):
    model = SizeChartRow
    extra = 0
    autocomplete_fields = ["size"]


@admin.register(SizeChart)
class SizeChartAdmin(admin.ModelAdmin):
    list_display = ["name", "size_system"]
    search_fields = ["name"]
    inlines = [SizeChartRowInline]


@admin.register(MeasurementDefinition)
class MeasurementDefinitionAdmin(admin.ModelAdmin):
    list_display = ["label", "key", "applies_to", "min_cm", "max_cm", "position"]
    list_filter = ["applies_to"]
    search_fields = ["label", "key"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}
