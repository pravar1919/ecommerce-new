from django.contrib import admin

from .models import TaxClass, TaxRule


class TaxRuleInline(admin.TabularInline):
    model = TaxRule
    extra = 0


@admin.register(TaxClass)
class TaxClassAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]
    search_fields = ["name", "code"]
    inlines = [TaxRuleInline]
