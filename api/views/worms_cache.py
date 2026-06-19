"""ViewSet for WoRMS cache AJAX endpoints."""

from __future__ import annotations

from typing import Any

import requests
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
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


AJAX_BY_NAME_PART_PARAMETERS = [
    OpenApiParameter(
        name="name_part",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.PATH,
        required=True,
    ),
    OpenApiParameter(
        name="combine_vernaculars",
        type=OpenApiTypes.BOOL,
        required=False,
        description="Include vernacular matching.",
    ),
]


@extend_schema(tags=["Annotations API"])
class WormsCacheAjaxViewSet(GenericViewSet):
    """ViewSet for WoRMS cache AJAX endpoints."""

    @extend_schema(
        parameters=AJAX_BY_NAME_PART_PARAMETERS,
        responses={200: TaxonWormsLikeSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"ajax_by_name_part/(?P<name_part>[^/]+)",
        pagination_class=None,
        filter_backends=[],
    )
    def ajax_by_name_part(self, request: Request, name_part: str) -> Response:
        """Endpoint for AJAX autocomplete of taxon names."""
        results = _get_ajax_by_name_part_results(
            name_part=name_part,
            combine_vernaculars=_get_bool_query_param(request, "combine_vernaculars", default=True),
        )

        serializer = TaxonWormsLikeSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
