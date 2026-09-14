"""Taxonomy lookups backed by the cached WoRMS client."""

from __future__ import annotations

from typing import Any

import requests
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.services.cached_worms_client import CachedWoRMSClient


class TaxonWormsLikeSerializer(serializers.Serializer):
    """Serializer for a WoRMS-like taxon result."""

    AphiaID = serializers.IntegerField()
    scientificname = serializers.CharField()
    url = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    rank = serializers.CharField(required=False, allow_blank=True)
    valid_AphiaID = serializers.IntegerField(required=False, allow_null=True)
    valid_name = serializers.CharField(required=False, allow_blank=True)
    modified = serializers.DateTimeField(required=False, allow_null=True)
    cached_at = serializers.DateTimeField(required=False, allow_null=True)
    parent_AphiaID = serializers.IntegerField(required=False, allow_null=True)


def _get_ajax_by_name_part_results(
    *,
    name_part: str,
    combine_vernaculars: bool = True,
) -> list[dict[str, Any]]:
    """Get WoRMS-like taxon results for a given name part."""
    client = CachedWoRMSClient()

    try:
        results = client.ajax_by_name_part(
            name_part,
            combine_vernaculars=combine_vernaculars,
        )
    except requests.RequestException:
        return []

    if not results:
        return []

    if isinstance(results, dict):
        return list(results.values())

    return list(results)


def _get_bool_query_param(
    request: Request,
    name: str,
    default: bool = False,
) -> bool:
    """Read a boolean query parameter."""
    value = request.query_params.get(name)

    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "y", "on"}


@extend_schema(tags=["Taxonomy"])
class WormsTaxaViewSet(GenericViewSet):
    """Search WoRMS taxa by a partial name."""

    pagination_class = None
    filter_backends = []

    @extend_schema(
        summary="Find WoRMS taxa by partial name",
        parameters=[
            OpenApiParameter(name="name_part", type=OpenApiTypes.STR, required=True),
            OpenApiParameter(
                name="combine_vernaculars",
                type=OpenApiTypes.BOOL,
                required=False,
                description="Include vernacular matching.",
            ),
        ],
        responses={200: TaxonWormsLikeSerializer(many=True), 400: OpenApiTypes.OBJECT},
    )
    def list(self, request: Request) -> Response:
        """Return taxa matching the required name_part query parameter."""
        name_part = request.query_params.get("name_part", "").strip()
        if not name_part:
            return Response({"name_part": ["This query parameter is required and must not be blank."]}, status=400)
        results = _get_ajax_by_name_part_results(
            name_part=name_part,
            combine_vernaculars=_get_bool_query_param(request, "combine_vernaculars", default=True),
        )
        return Response(TaxonWormsLikeSerializer(results, many=True).data)
