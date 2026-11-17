from django.db.models import Prefetch
from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories import selectors as category_selectors
from apps.categories.models import Category

from .. import selectors
from ..models import MeasurementDefinition, SizeChart
from . import serializers as s

LISTING_PARAMS = [
    OpenApiParameter(name, str, description=f.help_text or None)
    for name, f in s.ProductQuerySerializer().fields.items()
]


class CategoryTreeView(APIView):
    @extend_schema(responses=s.CategoryNodeSerializer(many=True), tags=["catalog"])
    def get(self, request):
        cats = list(category_selectors.active_categories())
        children: dict = {}
        for c in cats:
            children.setdefault(c.parent_id, []).append(c)
        roots = children.get(None, [])
        return Response(s.CategoryNodeSerializer(roots, many=True, context={"children": children}).data)


class CategoryDetailView(APIView):
    @extend_schema(responses=s.CategoryDetailSerializer, tags=["catalog"])
    def get(self, request, path: str):
        cat = (
            Category.objects.filter(is_active=True, path=path.strip("/"))
            .select_related("parent__parent__parent")
            .prefetch_related(
                Prefetch(
                    "children", queryset=Category.objects.filter(is_active=True), to_attr="active_children"
                )
            )
            .first()
        )
        if cat is None:
            raise Http404
        return Response(s.CategoryDetailSerializer(cat).data)


class CollectionListView(generics.ListAPIView):
    serializer_class = s.CollectionSerializer
    pagination_class = None

    def get_queryset(self):
        return category_selectors.live_collections()

    @extend_schema(tags=["catalog"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CollectionDetailView(generics.RetrieveAPIView):
    serializer_class = s.CollectionSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return category_selectors.live_collections()

    @extend_schema(tags=["catalog"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductListView(generics.ListAPIView):
    """Product listing with filters and sorting. All amounts are paise."""

    serializer_class = s.ProductCardSerializer

    def get_queryset(self):
        params = s.ProductQuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        return selectors.list_products(params.to_filters())

    @extend_schema(parameters=LISTING_PARAMS, tags=["catalog"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductSearchView(ProductListView):
    throttle_scope = "search"

    @extend_schema(parameters=LISTING_PARAMS, tags=["catalog"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductFacetsView(APIView):
    @extend_schema(parameters=LISTING_PARAMS, responses=s.FacetsSerializer, tags=["catalog"])
    def get(self, request):
        params = s.ProductQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        return Response(selectors.product_facets(params.to_filters()))


def _published_or_404(slug: str):
    product = selectors.product_detail(slug)
    if product is None:
        raise Http404
    return product


class ProductDetailView(APIView):
    @extend_schema(responses=s.ProductDetailSerializer, tags=["catalog"])
    def get(self, request, slug: str):
        return Response(s.ProductDetailSerializer(_published_or_404(slug)).data)


class RelatedProductsView(APIView):
    @extend_schema(responses=s.ProductCardSerializer(many=True), tags=["catalog"])
    def get(self, request, slug: str):
        product = _published_or_404(slug)
        return Response(s.ProductCardSerializer(selectors.related_products(product), many=True).data)


class CompleteTheLookView(APIView):
    @extend_schema(responses=s.ProductCardSerializer(many=True), tags=["catalog"])
    def get(self, request, slug: str):
        product = _published_or_404(slug)
        return Response(s.ProductCardSerializer(selectors.complete_the_look(product), many=True).data)


class SearchSuggestView(APIView):
    throttle_scope = "search"

    @extend_schema(
        parameters=[OpenApiParameter("q", str, required=True)],
        responses=s.SuggestionsSerializer,
        tags=["catalog"],
    )
    def get(self, request):
        result = selectors.search_suggestions(request.query_params.get("q", "")[:100])
        products = []
        for p in result["products"]:
            card = s.ProductCardSerializer(p).data
            products.append(
                {"slug": p.slug, "name": p.name, "price": card["price"], "image": card["primary_image"]}
            )
        return Response(
            {
                "products": products,
                "categories": [{"name": c.name, "path": c.path} for c in result["categories"]],
                "queries": result["queries"],
            }
        )


class SizeChartView(generics.RetrieveAPIView):
    serializer_class = s.SizeChartSerializer
    queryset = SizeChart.objects.select_related("size_system")

    @extend_schema(tags=["catalog"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MeasurementGuideView(generics.ListAPIView):
    """Body-measurement guidance (how to measure) — distinct from garment size charts."""

    serializer_class = s.MeasurementDefinitionSerializer
    pagination_class = None

    def get_queryset(self):
        return MeasurementDefinition.objects.exclude(applies_to=MeasurementDefinition.AppliesTo.GARMENT)

    @extend_schema(tags=["catalog"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
