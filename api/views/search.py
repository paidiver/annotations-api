"""ViewSet for the Annotation model."""

import builtins

import requests
from django.db.models import F, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.models.annotation import AnnotationLabel
from api.serializers.search import GROUPED_SEARCH_RESULT_ROW, SEARCH_RESULT_ITEM
from api.services.cached_worms_client import CachedWoRMSClient

SEARCH_PARAMS = [
    OpenApiParameter(
        name="name_part",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Partial name to search for in labels",
    ),
    OpenApiParameter(
        name="aphia_ids[]",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        many=True,
        required=False,
        description="List of AphiaIDs to return",
    ),
    OpenApiParameter(
        name="include_descendants",
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        required=False,
        description="If true, include descendant taxa in the response.",
    ),
    OpenApiParameter(
        name="calculate_summary",
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        required=False,
        description="If true, include a summary of the search results.",
    ),
]

PAGINATION_PARAMS = [
    OpenApiParameter(
        name="page",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Page number.",
    ),
    OpenApiParameter(
        name="page_size",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Number of results per page.",
    ),
]

GROUPED_SEARCH_PARAMS = [*SEARCH_PARAMS, *PAGINATION_PARAMS]


@extend_schema(tags=["Annotations API"])
class AnnotationSearchViewSet(GenericViewSet):
    """ViewSet for searching Annotations."""

    queryset = AnnotationLabel.objects.none()

    @extend_schema(
        parameters=SEARCH_PARAMS,
        responses={200: SEARCH_RESULT_ITEM},
    )
    def list(self, request: Request) -> Response:
        """Search for Annotations based on query parameters.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response: A DRF Response object containing the search results.
        """
        calculate_summary = request.query_params.get("calculate_summary", "false").lower() == "true"
        aphia_ids = self._get_all_aphia_ids_from_request(request)
        if isinstance(aphia_ids, Response):
            return aphia_ids

        queryset = self._get_search_queryset(aphia_ids)
        summary = self._build_summary(queryset) if calculate_summary else None

        paginator = self.paginator
        page = paginator.paginate_queryset(queryset, request, view=self)
        response_data = {"summary": summary}

        if page is not None:
            response_data["annotations"] = page
            return paginator.get_paginated_response(response_data)
        response_data["annotations"] = list(queryset)
        return Response(response_data)

    @extend_schema(
        parameters=GROUPED_SEARCH_PARAMS,
        responses={200: GROUPED_SEARCH_RESULT_ROW},
    )
    @action(detail=False, methods=["get"], url_path="grouped")
    def list_grouped(self, request: Request) -> Response:
        """Search for Annotations based on query parameters.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response: A DRF Response object containing the search results.
        """
        calculate_summary = request.query_params.get("calculate_summary", "false").lower() == "true"
        aphia_ids = self._get_all_aphia_ids_from_request(request)
        if isinstance(aphia_ids, Response):
            return aphia_ids

        queryset = self._get_grouped_queryset(aphia_ids)
        summary = self._build_summary(queryset) if calculate_summary else None

        paginator = self.paginator
        page = paginator.paginate_queryset(queryset, request, view=self)

        rows = page if page is not None else list(queryset)
        grouped = {}
        for row in rows:
            annotation_set_uuid = str(row.pop("annotation_set_uuid"))
            grouped.setdefault(annotation_set_uuid, []).append(row)

        response_data = {
            "summary": summary,
            "annotations": grouped,
        }

        if page is not None:
            return paginator.get_paginated_response(response_data)
        return Response(response_data)

    def _get_search_queryset(self, aphia_ids: builtins.list[int]) -> QuerySet:
        """Get a queryset of Annotations matching the given AphiaIDs.

        Args:
            aphia_ids (list[int]): List of AphiaIDs to filter the Annotations by.

        Returns:
            QuerySet: A queryset of Annotations matching the given AphiaIDs.
        """
        return (
            AnnotationLabel.objects.filter(label__lowest_aphia_id__in=aphia_ids)
            .values(
                "creation_datetime",
                uuid=F("id"),
                image_filename=F("annotation__image__filename"),
                image_uuid=F("annotation__image__id"),
                label_name=F("label__name"),
                label_aphia_id=F("label__lowest_aphia_id"),
                annotation_platform=F("annotation__annotation_platform"),
                annotation_shape=F("annotation__shape"),
                annotation_coordinates=F("annotation__coordinates"),
                annotation_dimension_pixels=F("annotation__dimension_pixels"),
                annotator_name=F("annotator__name"),
                annotation_set_uuid=F("annotation__annotation_set__id"),
                annotation_set_name=F("annotation__annotation_set__name"),
                image_set_uuid=F("annotation__image__image_set__id"),
                image_set_name=F("annotation__image__image_set__name"),
            )
            .order_by("annotation__annotation_set__name", "annotation__image__image_set__name", "id")
        )

    def _get_grouped_queryset(self, aphia_ids: builtins.list[int]) -> QuerySet:
        """Get a queryset of Annotations grouped by annotation set and image set.

        Args:
            aphia_ids (list[int]): List of AphiaIDs to filter the Annotations by.

        Returns:
            QuerySet: A queryset of Annotations grouped by annotation set and image set.
        """
        return (
            AnnotationLabel.objects.filter(label__lowest_aphia_id__in=aphia_ids)
            .values(
                "creation_datetime",
                uuid=F("id"),
                annotation_set_uuid=F("annotation__annotation_set__id"),
                annotation_set_name=F("annotation__annotation_set__name"),
                image_set_name=F("annotation__image__image_set__name"),
                image_set_uuid=F("annotation__image__image_set__id"),
                image_filename=F("annotation__image__filename"),
                image_uuid=F("annotation__image__id"),
                label_name=F("label__name"),
                label_aphia_id=F("label__lowest_aphia_id"),
                annotation_platform=F("annotation__annotation_platform"),
                annotation_shape=F("annotation__shape"),
                annotation_coordinates=F("annotation__coordinates"),
                annotation_dimension_pixels=F("annotation__dimension_pixels"),
                annotator_name=F("annotator__name"),
            )
            .order_by("annotation__annotation_set__id", "annotation__image__image_set__name", "id")
        )

    def _get_all_aphia_ids_from_request(self, request: Request) -> builtins.list[int] | Response:
        """Extract and validate a list of AphiaIDs from the query parameters, including descendants if requested.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            list[int] | Response: A list of valid AphiaIDs extracted from the query parameters or a Response in case of
        an error.
        """
        aphia_ids = self._get_aphia_ids_from_query(request)
        name_part = request.query_params.get("name_part")
        include_descendants = request.query_params.get("include_descendants", "false").lower() == "true"
        if not aphia_ids and not name_part:
            return Response(
                {"detail": "Please provide either 'aphia_ids' or 'name_part' query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if name_part:
            aphia_ids.extend(_get_aphia_ids_by_name_part(name_part) or [])

        aphia_ids = list(dict.fromkeys(aphia_ids))

        if not aphia_ids:
            return Response(
                {"detail": "No valid AphiaIDs found for the provided query parameters."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if include_descendants:
            descendant_ids = _get_descendant_aphia_ids(aphia_ids) or []
            aphia_ids = list(dict.fromkeys([*aphia_ids, *descendant_ids]))

        return aphia_ids

    def _get_aphia_ids_from_query(self, request: Request) -> builtins.list[int]:
        """Extract and validate a list of AphiaIDs from the query parameters."""
        raw_ids = request.query_params.getlist("aphia_ids[]")
        aphia_ids = []
        for value in raw_ids:
            try:
                aphia_ids.append(int(value))
            except (TypeError, ValueError):
                continue
        return aphia_ids

    def _build_summary(self, queryset: QuerySet) -> dict:
        """Build summary statistics for a queryset.

        Args:
            queryset (QuerySet): The queryset to build the summary for.

        Returns:
            dict: A dictionary containing summary statistics.
        """
        return {
            "n_annotations": queryset.count(),
            "n_images": queryset.values("annotation__image__id").distinct().count(),
            "n_annotation_sets": queryset.values("annotation__annotation_set__id").distinct().count(),
            "n_image_sets": queryset.values("annotation__image__image_set__id").distinct().count(),
        }


def _get_descendant_aphia_ids(aphia_ids: list[int]) -> list[int]:
    """Get descendant AphiaIDs for a list of AphiaIDs.

    Args:
        aphia_ids (list[int]): List of AphiaIDs to get descendants for.

    Returns:
        list[int]: List of descendant AphiaIDs.
    """
    client = CachedWoRMSClient()
    try:
        return client.descendants_aphia_ids(aphia_ids) or []
    except requests.RequestException:
        return []


def _get_aphia_ids_by_name_part(name_part: str) -> list[str]:
    """Get AphiaIDs for a given name part.

    Args:
        name_part (str): The name part to search for.

    Returns:
        list[str]: List of AphiaIDs matching the name part.
    """
    client = CachedWoRMSClient()
    try:
        return client.aphia_ids_by_name_part(name_part, combine_vernaculars=True) or []
    except requests.RequestException:
        return []
