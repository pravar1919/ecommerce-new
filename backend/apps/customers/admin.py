from django.contrib import admin

from .models import Address, CustomerProfile, MeasurementProfile


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0


class MeasurementInline(admin.StackedInline):
    model = MeasurementProfile
    extra = 0


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "marketing_email_opt_in", "created_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    raw_id_fields = ["user"]
    inlines = [AddressInline, MeasurementInline]
