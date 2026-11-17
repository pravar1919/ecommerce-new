from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("addresses", views.AddressViewSet, basename="address")
router.register("measurements", views.MeasurementProfileViewSet, basename="measurement")

urlpatterns = [path("profile/", views.ProfileView.as_view(), name="account-profile"), *router.urls]
