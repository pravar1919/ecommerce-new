from django.urls import path

from . import views

urlpatterns = [
    path("site-settings/", views.SiteSettingsView.as_view(), name="cms-site-settings"),
    path("navigation/", views.NavigationView.as_view(), name="cms-navigation"),
    path("pages/<slug:slug>/", views.PageView.as_view(), name="cms-page"),
    path("newsletter/", views.NewsletterSignupView.as_view(), name="cms-newsletter"),
    path("newsletter/confirm/", views.NewsletterConfirmView.as_view(), name="cms-newsletter-confirm"),
    path(
        "newsletter/unsubscribe/",
        views.NewsletterUnsubscribeView.as_view(),
        name="cms-newsletter-unsubscribe",
    ),
]
