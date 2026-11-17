from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import selectors, services
from ..models import PageVersion
from . import serializers as s


class SiteSettingsView(APIView):
    """Brand configuration, announcement bar, footer and social links."""

    @extend_schema(responses=s.SiteSettingsOutSerializer, tags=["cms"])
    def get(self, request):
        return Response(selectors.site_settings_dict())


class NavigationView(APIView):
    """Mega-menu: top-level categories with children, editorial feature tiles, live collections."""

    @extend_schema(responses=s.NavigationOutSerializer, tags=["cms"])
    def get(self, request):
        return Response(selectors.navigation_dict())


class PageView(APIView):
    """The published version of a page. Staff may preview any version with `?version=<id>`."""

    @extend_schema(
        parameters=[OpenApiParameter("version", str, required=False, description="Staff-only preview")],
        responses=s.PageOutSerializer,
        tags=["cms"],
    )
    def get(self, request, slug: str):
        version_id = request.query_params.get("version")
        if version_id:
            if not (request.user.is_authenticated and request.user.is_staff):
                raise Http404
            version = (
                PageVersion.objects.filter(page__slug=slug, pk=version_id)
                .select_related("page__og_image")
                .first()
                if selectors.parse_uuids([version_id])
                else None
            )
        else:
            version = selectors.published_version(slug)
        if version is None:
            raise Http404
        response = Response(selectors.page_dict(version))
        if version_id:
            response["Cache-Control"] = "private, no-store"
        return response


class NewsletterSignupView(APIView):
    throttle_scope = "newsletter"

    @extend_schema(
        request=s.NewsletterSignupSerializer, responses={202: s.NewsletterStatusSerializer}, tags=["cms"]
    )
    def post(self, request):
        body = s.NewsletterSignupSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        services.subscribe(email=body.validated_data["email"], source=body.validated_data["source"])
        # Same response whether or not the address already exists (no enumeration).
        return Response({"status": "pending"}, status=status.HTTP_202_ACCEPTED)


class NewsletterConfirmView(APIView):
    throttle_scope = "newsletter"

    @extend_schema(request=s.NewsletterTokenSerializer, responses=s.NewsletterStatusSerializer, tags=["cms"])
    def post(self, request):
        body = s.NewsletterTokenSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        sub = services.confirm_subscription(token=body.validated_data["token"])
        return Response({"status": sub.status})


class NewsletterUnsubscribeView(APIView):
    throttle_scope = "newsletter"

    @extend_schema(request=s.NewsletterTokenSerializer, responses=s.NewsletterStatusSerializer, tags=["cms"])
    def post(self, request):
        body = s.NewsletterTokenSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        sub = services.unsubscribe(token=body.validated_data["token"])
        return Response({"status": sub.status})
