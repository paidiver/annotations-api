"""Reusable query-parameter filtering for set index endpoints."""

from django.db.models import QuerySet
from rest_framework.request import Request


def filter_set_queryset(
    queryset: QuerySet,
    request: Request,
    text_fields: dict[str, str],
) -> QuerySet:
    """Apply case-insensitive partial text filters and an exact UUID filter."""
    uuid_value = request.query_params.get("uuid", "").strip()
    if uuid_value:
        queryset = queryset.filter(id=uuid_value)

    for parameter, model_field in text_fields.items():
        value = request.query_params.get(parameter, "").strip()
        if value:
            queryset = queryset.filter(**{f"{model_field}__icontains": value})

    return queryset
