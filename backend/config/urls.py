from django.conf import settings
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = f"{settings.BRAND_NAME} · internal admin"
admin.site.site_title = f"{settings.BRAND_NAME} admin"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/", include("config.api_urls")),
]
