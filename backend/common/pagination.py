from rest_framework import pagination


class PageNumberPagination(pagination.PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 96
