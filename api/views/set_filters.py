"""Reusable query-parameter filtering for set index endpoints."""

from django.db.models import CharField, QuerySet
from django.db.models.functions import Cast
from rest_framework.request import Request


def filter_set_queryset(
    queryset: QuerySet,
    request: Request,
    text_fields: dict[str, str],
) -> QuerySet:
    """Apply case-insensitive partial text filters and a partial UUID filter."""
    uuid_value = request.query_params.get("uuid", "").strip()
    if uuid_value:
        queryset = queryset.alias(id_as_text=Cast("id", output_field=CharField()))
        queryset = queryset.filter(id_as_text__icontains=uuid_value)

    for parameter, model_field in text_fields.items():
        value = request.query_params.get(parameter, "").strip()
        if value:
            queryset = queryset.filter(**{f"{model_field}__icontains": value})

    return queryset
