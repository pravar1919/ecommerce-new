from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.CategoryTreeView.as_view(), name="category-tree"),
    path("categories/<path:path>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("collections/", views.CollectionListView.as_view(), name="collection-list"),
    path("collections/<slug:slug>/", views.CollectionDetailView.as_view(), name="collection-detail"),
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/facets/", views.ProductFacetsView.as_view(), name="product-facets"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("products/<slug:slug>/related/", views.RelatedProductsView.as_view(), name="product-related"),
    path("products/<slug:slug>/complete-the-look/", views.CompleteTheLookView.as_view(), name="product-look"),
    path("search/", views.ProductSearchView.as_view(), name="product-search"),
    path("search/suggest/", views.SearchSuggestView.as_view(), name="search-suggest"),
    path("size-charts/<uuid:pk>/", views.SizeChartView.as_view(), name="size-chart"),
    path("measurement-guide/", views.MeasurementGuideView.as_view(), name="measurement-guide"),
]
