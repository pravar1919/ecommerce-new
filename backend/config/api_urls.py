from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, IsAdminUser

from common.health import HealthView, LivenessView

docs_permission = [IsAdminUser] if settings.ENVIRONMENT == "production" else [AllowAny]

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("health/live/", LivenessView.as_view(), name="health-live"),
    path("schema/", SpectacularAPIView.as_view(permission_classes=docs_permission), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=docs_permission)),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema", permission_classes=docs_permission)),
    path("auth/", include("apps.accounts.api.urls")),
    path("auth/", include("apps.customers.api.auth_urls")),
    path("account/", include("apps.customers.api.urls")),
    path("catalog/", include("apps.catalog.api.urls")),
]
