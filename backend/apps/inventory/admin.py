from django import forms
from django.contrib import admin

from apps.catalog.models import ProductVariant

from . import services
from .models import LowStockAlert, StockLevel, StockLocation, StockMovement, StockReservation


@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "state_code", "is_default", "is_active"]


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ["variant", "location", "on_hand", "reserved", "available", "low_stock_threshold"]
    list_filter = ["location"]
    search_fields = ["variant__sku", "variant__product__name"]
    readonly_fields = ["variant", "location", "on_hand", "reserved"]
    fields = ["variant", "location", "on_hand", "reserved", "low_stock_threshold"]

    def has_add_permission(self, request):
        return False  # created by stock adjustments

    def has_delete_permission(self, request, obj=None):
        return False


class AdjustmentForm(forms.ModelForm):
    variant = forms.ModelChoiceField(queryset=ProductVariant.objects.select_related("product"))
    location = forms.ModelChoiceField(
        queryset=StockLocation.objects.filter(is_active=True),
        required=False,
        help_text="Defaults to the default location",
    )

    class Meta:
        model = StockMovement
        fields = ["variant", "location", "delta", "reason", "note"]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Add = record a stock adjustment through the inventory service. History is read-only."""

    list_display = ["created_at", "stock_level", "delta", "reason", "balance_after", "actor", "note"]
    list_filter = ["reason", "stock_level__location"]
    search_fields = ["stock_level__variant__sku", "reference_id", "note"]
    form = AdjustmentForm

    def get_form(self, request, obj=None, **kwargs):
        if obj is not None:
            kwargs["form"] = forms.ModelForm
            kwargs["fields"] = []
        return super().get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return [
                "stock_level",
                "delta",
                "reason",
                "balance_after",
                "reference_type",
                "reference_id",
                "actor",
                "note",
                "created_at",
            ]
        return []

    def save_model(self, request, obj, form, change):
        if change:
            return
        cd = form.cleaned_data
        level = services.adjust_stock(
            variant_id=cd["variant"].pk,
            delta=cd["delta"],
            reason=cd["reason"],
            location=cd.get("location"),
            actor=request.user,
            note=cd.get("note", ""),
        )
        latest = level.movements.order_by("-created_at").first()
        obj.pk = latest.pk
        obj._state.adding = False

    def has_change_permission(self, request, obj=None):
        return obj is None and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ["stock_level", "quantity", "status", "owner_type", "owner_id", "expires_at"]
    list_filter = ["status", "owner_type"]
    readonly_fields = [f.name for f in StockReservation._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display = ["stock_level", "available_at_trigger", "created_at", "resolved_at"]
    list_filter = ["resolved_at"]
