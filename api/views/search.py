"""ViewSet for the Annotation model."""

from __future__ import annotations

import requests
from django.db.models import F, Q, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.models.annotation import AnnotationLabel
from api.models.base import DeploymentEnum, FaunaAttractionEnum, MarineZoneEnum
from api.serializers.search import GroupedSearchResultRow, SearchResultItem
from api.services.cached_worms_client import CachedWoRMSClient

DEPLOYMENT_VALUES = [item.value for item in DeploymentEnum]
FAUNA_ATTRACTION_VALUES = [item.value for item in FaunaAttractionEnum]
MARINE_ZONE_VALUES = [item.value for item in MarineZoneEnum]

SEARCH_PARAMS = [
    OpenApiParameter(
        name="name_part",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Partial name to search for in labels. Must contain at least 3 characters.",
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
    OpenApiParameter(
        name="image_set_name",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Partial image set name to filter results. Must contain at least 3 characters.",
    ),
    OpenApiParameter(
        name="project",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Partial project name to filter results. Must contain at least 3 characters.",
    ),
    OpenApiParameter(
        name="platform",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Partial platform name to filter results. Must contain at least 3 characters.",
    ),
    OpenApiParameter(
        name="deployment",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        enum=DEPLOYMENT_VALUES,
        description="Deployment filter. Must be one of the allowed deployment values.",
    ),
    OpenApiParameter(
        name="fauna_attraction",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        enum=FAUNA_ATTRACTION_VALUES,
        description="Fauna attraction filter. Must be one of the allowed values.",
    ),
    OpenApiParameter(
        name="marine_zone",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        enum=MARINE_ZONE_VALUES,
        description="Marine zone filter. Must be one of the allowed values.",
    ),
    OpenApiParameter(
        name="min_lat",
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Minimum latitude in EPSG:4326 degrees.",
    ),
    OpenApiParameter(
        name="max_lat",
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Maximum latitude in EPSG:4326 degrees.",
    ),
    OpenApiParameter(
        name="min_lon",
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Minimum longitude in EPSG:4326 degrees.",
    ),
    OpenApiParameter(
        name="max_lon",
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Maximum longitude in EPSG:4326 degrees.",
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
        responses={200: SearchResultItem, 204: None},
    )
    def list(self, request: Request) -> Response:
        """Search for Annotations based on query parameters.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response: A DRF Response object containing the search results.
        """
        validation_error = self._validate_search_params(request)
        if validation_error is not None:
            return validation_error
        aphia_ids = self._get_all_aphia_ids_from_request(request)
        if isinstance(aphia_ids, Response):
            return aphia_ids
        queryset = self._get_search_queryset(aphia_ids=aphia_ids, request=request)

        calculate_summary = request.query_params.get("calculate_summary", "false").lower() == "true"
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
        responses={200: GroupedSearchResultRow, 204: None},
    )
    @action(detail=False, methods=["get"], url_path="grouped")
    def list_grouped(self, request: Request) -> Response:
        """Search for Annotations based on query parameters.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response: A DRF Response object containing the search results.
        """
        validation_error = self._validate_search_params(request)
        if validation_error is not None:
            return validation_error
        aphia_ids = self._get_all_aphia_ids_from_request(request)
        if isinstance(aphia_ids, Response):
            return aphia_ids

        queryset = self._get_search_queryset(aphia_ids=aphia_ids, request=request)

        calculate_summary = request.query_params.get("calculate_summary", "false").lower() == "true"
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

    def _get_search_queryset(self, aphia_ids: list[int], request: Request) -> QuerySet:
        """Get a queryset of Annotations matching the given AphiaIDs.

        Args:
            aphia_ids (list[int]): List of AphiaIDs to filter the Annotations by.
            request (Request): The incoming HTTP request containing additional query parameters.


        Returns:
            QuerySet: A queryset of Annotations matching the given AphiaIDs.
        """
        filters = self._calculate_filters(aphia_ids, request)
        return (
            AnnotationLabel.objects.filter(filters)
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
            .order_by("annotation__annotation_set__name", "annotation__image__image_set__name", "id")
        )

    def _calculate_filters(self, aphia_ids: list[int], request: Request) -> Q:
        """Calculate the filters to apply to the Annotation queryset based on the query parameters.

        Args:
            aphia_ids (list[int]): List of AphiaIDs to filter the Annotations by.
            request (Request): The incoming HTTP request containing additional query parameters.

        Returns:
            Q: A Django Q object representing the filters to apply to the Annotation queryset.
        """
        min_lat = self._get_float_query_param(request, "min_lat")
        max_lat = self._get_float_query_param(request, "max_lat")
        min_lon = self._get_float_query_param(request, "min_lon")
        max_lon = self._get_float_query_param(request, "max_lon")
        name_part = request.query_params.get("name_part")
        image_set_name = request.query_params.get("image_set_name")
        project = request.query_params.get("project")
        platform = request.query_params.get("platform")
        deployment = request.query_params.get("deployment")
        fauna_attraction = request.query_params.get("fauna_attraction")
        marine_zone = request.query_params.get("marine_zone")

        if aphia_ids and name_part:
            name_part = name_part.strip()
            filters = Q(Q(label__lowest_aphia_id__in=aphia_ids) | Q(label__name__icontains=name_part))
        else:
            filters = Q()
            if aphia_ids:
                filters &= Q(label__lowest_aphia_id__in=aphia_ids)
            if name_part:
                name_part = name_part.strip()
                filters &= Q(label__name__icontains=name_part)
        if image_set_name:
            image_set_name = image_set_name.strip()
            filters &= Q(annotation__image__image_set__name__icontains=image_set_name)

        if project:
            project = project.strip()
            filters &= Q(annotation__image__image_set__project__name__icontains=project)
        if platform:
            platform = platform.strip()
            filters &= Q(annotation__image__image_set__platform__name__icontains=platform)
        if deployment:
            deployment = deployment.strip()
            filters &= Q(annotation__image__image_set__deployment=deployment)
        if fauna_attraction:
            fauna_attraction = fauna_attraction.strip()
            filters &= Q(annotation__image__image_set__fauna_attraction=fauna_attraction)
        if marine_zone:
            marine_zone = marine_zone.strip()
            filters &= Q(annotation__image__image_set__marine_zone=marine_zone)
        if min_lat is not None:
            filters &= Q(annotation__image__latitude__gte=min_lat)
        if max_lat is not None:
            filters &= Q(annotation__image__latitude__lte=max_lat)
        if min_lon is not None:
            filters &= Q(annotation__image__longitude__gte=min_lon)
        if max_lon is not None:
            filters &= Q(annotation__image__longitude__lte=max_lon)
        return filters

    def _validate_search_params(self, request: Request) -> Response | None:
        """Validate the search query parameters.

        Args:
            request (Request): The incoming HTTP request containing the query parameters.

        Returns:
            Response | None: A DRF Response object with an error message if validation fails, or None if validation passes.
        """
        choices_map = {
            "deployment": set(DEPLOYMENT_VALUES),
            "fauna_attraction": set(FAUNA_ATTRACTION_VALUES),
            "marine_zone": set(MARINE_ZONE_VALUES),
        }
        errors = {}

        for param_name, allowed_values in choices_map.items():
            value = request.query_params.get(param_name)
            if value and value not in allowed_values:
                errors[param_name] = (
                    f"Invalid value for '{param_name}': '{value}'. " f"Allowed values are: {sorted(allowed_values)}"
                )
        aphia_ids = self._get_aphia_ids_from_query(request)
        name_part = request.query_params.get("name_part")
        if not aphia_ids and not name_part:
            errors["query"] = "At least one of 'aphia_ids[]' or 'name_part' query parameters must be provided."
        length_limit_params = ["name_part", "project", "platform", "image_set_name"]
        for param_name in length_limit_params:
            value = request.query_params.get(param_name)
            if value and len(value.strip()) < 3:
                errors[param_name] = f"'{param_name}' must contain at least 3 characters."

        bbox_values = {}
        for param_name in ["min_lat", "max_lat", "min_lon", "max_lon"]:
            raw_value = request.query_params.get(param_name)
            if raw_value in (None, ""):
                bbox_values[param_name] = None
                continue
            try:
                bbox_values[param_name] = float(raw_value)
            except (TypeError, ValueError):
                errors[param_name] = f"'{param_name}' must be a valid number."

        min_lat = bbox_values.get("min_lat")
        max_lat = bbox_values.get("max_lat")
        min_lon = bbox_values.get("min_lon")
        max_lon = bbox_values.get("max_lon")

        if min_lat is not None and not (-90 <= min_lat <= 90):
            errors["min_lat"] = "'min_lat' must be between -90 and 90."
        if max_lat is not None and not (-90 <= max_lat <= 90):
            errors["max_lat"] = "'max_lat' must be between -90 and 90."
        if min_lon is not None and not (-180 <= min_lon <= 180):
            errors["min_lon"] = "'min_lon' must be between -180 and 180."
        if max_lon is not None and not (-180 <= max_lon <= 180):
            errors["max_lon"] = "'max_lon' must be between -180 and 180."

        if min_lat is not None and max_lat is not None and min_lat > max_lat:
            errors["latitude_range"] = "'min_lat' must be less than or equal to 'max_lat'."
        if min_lon is not None and max_lon is not None and min_lon > max_lon:
            errors["longitude_range"] = "'min_lon' must be less than or equal to 'max_lon'."

        if errors:
            return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

        return None

    def _get_all_aphia_ids_from_request(self, request: Request) -> list[int] | Response:
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
        if name_part:
            name_part = name_part.strip()
            aphia_ids.extend(_get_aphia_ids_by_name_part(name_part) or [])

        aphia_ids = list(dict.fromkeys(aphia_ids))

        if not aphia_ids:
            return (
                Response(
                    {"detail": "No valid AphiaIDs found for the provided query parameters."},
                    status=status.HTTP_404_NOT_FOUND,
                )
                if not name_part
                else []
            )

        if include_descendants:
            descendant_ids = _get_descendant_aphia_ids(aphia_ids) or []
            aphia_ids = list(dict.fromkeys([*aphia_ids, *descendant_ids]))

        return aphia_ids

    def _get_float_query_param(self, request: Request, name: str) -> float | None:
        """Extract a float query parameter."""
        value = request.query_params.get(name)
        if value in (None, ""):
            return None
        return float(value)

    def _get_aphia_ids_from_query(self, request: Request) -> list[int]:
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


def _get_aphia_ids_by_name_part(name_part: str) -> list[int]:
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
