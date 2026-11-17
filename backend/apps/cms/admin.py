"""Break-glass admin for content. The operational page builder is the Next.js admin (Phase 6)."""

from django.contrib import admin, messages
from django.utils.html import format_html

from common.exceptions import DomainError

from . import services
from .models import (
    ContentBlock,
    MediaAsset,
    NavigationFeature,
    NewsletterSubscriber,
    Page,
    PageVersion,
    SiteSettings,
    Testimonial,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ["brand_name", "theme_key", "updated_at"]
    autocomplete_fields = ["logo"]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        services.site_settings_changed()


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ["thumb", "alt_text", "kind", "width", "height", "is_placeholder", "created_at"]
    list_filter = ["kind", "is_placeholder"]
    search_fields = ["alt_text", "credit", "tags"]
    readonly_fields = ["is_product_photo"]

    @admin.display(description="")
    def thumb(self, obj):
        if obj.kind == MediaAsset.Kind.IMAGE and obj.file:
            return format_html('<img src="{}" style="height:48px" alt="">', obj.file.url)
        return "—"


class BlockInline(admin.StackedInline):
    model = ContentBlock
    extra = 0
    fields = ["type", "position", "config", "visible_from", "visible_until"]


@admin.register(PageVersion)
class PageVersionAdmin(admin.ModelAdmin):
    list_display = ["page", "version", "status", "publish_at", "published_at", "note"]
    list_filter = ["status", "page"]
    readonly_fields = ["version", "published_at", "published_by"]
    inlines = [BlockInline]
    actions = ["publish", "duplicate_as_draft"]

    def get_readonly_fields(self, request, obj=None):
        # Status changes go through the publish service, never a raw edit.
        return [*self.readonly_fields, "status"] if obj else self.readonly_fields

    @admin.action(description="Publish selected version")
    def publish(self, request, queryset):
        for v in queryset:
            try:
                services.publish_version(v, actor=request.user)
                self.message_user(request, f"Published {v}.")
            except DomainError as exc:
                self.message_user(request, f"{v}: {exc.message} {exc.fields or ''}", messages.ERROR)

    @admin.action(description="Duplicate as a new draft")
    def duplicate_as_draft(self, request, queryset):
        for v in queryset:
            draft = services.create_draft(v.page, from_version=v, note=f"Copy of v{v.version}")
            self.message_user(request, f"Created {draft}.")


class VersionInline(admin.TabularInline):
    model = PageVersion
    extra = 0
    fields = ["version", "status", "publish_at", "published_at", "note"]
    readonly_fields = ["version", "status", "published_at"]
    show_change_link = True


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["slug", "title", "template"]
    search_fields = ["slug", "title"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [VersionInline]


@admin.register(NavigationFeature)
class NavigationFeatureAdmin(admin.ModelAdmin):
    list_display = ["category_path", "title", "href", "position", "is_active"]
    list_filter = ["is_active"]
    autocomplete_fields = ["media"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        services.navigation_changed()


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["name", "occasion", "is_published", "is_placeholder", "consent_recorded_at"]
    list_filter = ["is_published", "is_placeholder"]
    search_fields = ["name", "quote"]
    autocomplete_fields = ["media"]


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "status", "source", "confirmed_at", "created_at"]
    list_filter = ["status", "source"]
    search_fields = ["email"]
    readonly_fields = ["consented_at", "confirmed_at", "unsubscribed_at"]
