"""Reusable query-parameter filtering for set index endpoints."""

from django.db.models import CharField, Q, QuerySet
from django.db.models.functions import Cast
from rest_framework.request import Request


def filter_by_any_text_field(queryset: QuerySet, value: str, model_fields: list[str]) -> QuerySet:
    """Apply a case-insensitive partial search that matches any of the provided fields."""
    search_value = value.strip()
    if not search_value or not model_fields:
        return queryset

    matching_fields = Q()
    for model_field in model_fields:
        matching_fields |= Q(**{f"{model_field}__icontains": search_value})

    return queryset.filter(matching_fields)


def filter_set_queryset(
    queryset: QuerySet,
    request: Request,
    text_fields: dict[str, str],
    metadata_search_fields: list[str],
) -> QuerySet:
    """Apply a grouped any-field search, individual text filters, and a partial UUID filter."""
    uuid_value = request.query_params.get("uuid", "").strip()
    if uuid_value:
        queryset = queryset.alias(id_as_text=Cast("id", output_field=CharField()))
        queryset = queryset.filter(id_as_text__icontains=uuid_value)

    queryset = filter_by_any_text_field(
        queryset,
        request.query_params.get("metadata_search", ""),
        metadata_search_fields,
    )

    for parameter, model_field in text_fields.items():
        value = request.query_params.get(parameter, "").strip()
        if value:
            queryset = queryset.filter(**{f"{model_field}__icontains": value})

    return queryset
