"""This module defines a custom pagination class for the Annotations API, extending DRF's PageNumber."""

from rest_framework.pagination import PageNumberPagination


class DefaultPageNumberPagination(PageNumberPagination):
    """Custom pagination class that extends DRF's PageNumberPagination with default settings for the Annotations API."""

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500
