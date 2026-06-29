"""ViewSet for the Annotation model."""

from __future__ import annotations

import uuid

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
from api.serializers.search import GroupedSearchResultRow, PaginatedSearchResult
from api.services.cached_worms_client import CachedWoRMSClient

MIN_CHARS_FOR_PARTIAL_MATCH = 3

DEPLOYMENT_VALUES = [item.value for item in DeploymentEnum]
FAUNA_ATTRACTION_VALUES = [item.value for item in FaunaAttractionEnum]
MARINE_ZONE_VALUES = [item.value for item in MarineZoneEnum]

EXCLUDE_PARAMS = [
    OpenApiParameter(
        name="exclude_aphia_ids[]",
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="List of AphiaIDs to exclude from the search results.",
    ),
    OpenApiParameter(
        name="exclude_annotation_set[]",
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="List of annotation set IDs to exclude from the search results.",
    ),
    OpenApiParameter(
        name="exclude_image_set[]",
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="List of image set IDs to exclude from the search results.",
    ),
]

COORD_PARAMS = [
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
        name="return_image_annotation_name_info",
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        required=False,
        description="If true, include image and annotation set information in the response.",
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
    *COORD_PARAMS,
    *EXCLUDE_PARAMS,
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


EXPORT_PARAMS = [
    OpenApiParameter(
        name="disable_pagination",
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        required=False,
        description=("If true, return all matching annotations in a single response. Intended for export workflows."),
    ),
]

GROUPED_SEARCH_PARAMS = [*SEARCH_PARAMS, *PAGINATION_PARAMS]
LIST_SEARCH_PARAMS = [*SEARCH_PARAMS, *PAGINATION_PARAMS, *EXPORT_PARAMS]


@extend_schema(tags=["Annotations API"])
class AnnotationSearchViewSet(GenericViewSet):
    """ViewSet for searching Annotations."""

    queryset = AnnotationLabel.objects.none()

    @extend_schema(
        parameters=LIST_SEARCH_PARAMS,
        responses={200: PaginatedSearchResult, 204: None},
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
        aphia_ids_info = self._get_all_aphia_ids_from_request(request)
        if isinstance(aphia_ids_info, Response):
            return aphia_ids_info
        aphia_ids = list(aphia_ids_info.keys())
        filtered_queryset = self._get_filtered_queryset(aphia_ids=aphia_ids, request=request)
        queryset = self._get_search_queryset(filtered_queryset)

        calculate_summary = request.query_params.get("calculate_summary", "false").lower() == "true"
        summary = self._build_summary(queryset) if calculate_summary else None
        include_name_info = request.query_params.get("return_image_annotation_name_info", "false").lower() == "true"
        info = self._build_info(filtered_queryset, aphia_ids_info) if include_name_info else None

        response_data = {}
        if summary is not None:
            response_data["summary"] = summary
        if info is not None:
            response_data["info"] = info

        if self._disable_pagination_requested(request):
            response_data["annotations"] = list(queryset)
            return Response(response_data)

        paginator = self.paginator
        page = paginator.paginate_queryset(queryset, request, view=self)

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
        aphia_ids_info = self._get_all_aphia_ids_from_request(request)
        if isinstance(aphia_ids_info, Response):
            return aphia_ids_info
        aphia_ids = list(aphia_ids_info.keys())

        filtered_queryset = self._get_filtered_queryset(aphia_ids=aphia_ids, request=request)
        queryset = self._get_search_queryset(filtered_queryset)

        calculate_summary = request.query_params.get("calculate_summary", "false").lower() == "true"
        summary = self._build_summary(queryset) if calculate_summary else None
        include_name_info = request.query_params.get("return_image_annotation_name_info", "false").lower() == "true"
        info = self._build_info(filtered_queryset, aphia_ids_info) if include_name_info else None

        paginator = self.paginator
        page = paginator.paginate_queryset(queryset, request, view=self)

        rows = page if page is not None else list(queryset)
        grouped = {}
        for row in rows:
            annotation_set_uuid = str(row.pop("annotation_set_uuid"))
            grouped.setdefault(annotation_set_uuid, []).append(row)

        response_data = {
            "annotations": grouped,
        }
        if summary is not None:
            response_data["summary"] = summary
        if info is not None:
            response_data["info"] = info

        if page is not None:
            return paginator.get_paginated_response(response_data)
        return Response(response_data)

    def _get_filtered_queryset(self, aphia_ids: list[int], request: Request) -> QuerySet:
        """Get a filtered queryset of AnnotationLabel rows for the search request.

        Args:
            aphia_ids (list[int]): List of AphiaIDs to filter the Annotations by.
            request (Request): The incoming HTTP request containing additional query parameters.


        Returns:
            QuerySet: A filtered queryset of AnnotationLabel rows.
        """
        filters = self._calculate_filters(aphia_ids, request)
        return AnnotationLabel.objects.filter(filters)

    def _get_search_queryset(self, filtered_queryset: QuerySet) -> QuerySet:
        """Build the projected queryset returned by search endpoints.

        Args:
            filtered_queryset (QuerySet): A filtered queryset of AnnotationLabel rows.

        Returns:
            QuerySet: A projected queryset with response fields.
        """
        return filtered_queryset.values(
            "creation_datetime",
            uuid=F("id"),
            annotation_set_uuid=F("annotation__annotation_set__id"),
            annotation_set_name=F("annotation__annotation_set__name"),
            image_set_name=F("annotation__image__image_set__name"),
            image_set_uuid=F("annotation__image__image_set__id"),
            image_filename=F("annotation__image__filename"),
            image_handle=F("annotation__image__handle"),
            image_uuid=F("annotation__image__id"),
            label_name=F("label__name"),
            label_aphia_id=F("label__lowest_aphia_id"),
            annotation_platform=F("annotation__annotation_platform"),
            annotation_creation_datetime=F("creation_datetime"),
            annotation_shape=F("annotation__shape"),
            annotation_coordinates=F("annotation__coordinates"),
            annotation_dimension_pixels=F("annotation__dimension_pixels"),
            annotator_name=F("annotator__name"),
        ).order_by("annotation__annotation_set__name", "annotation__image__image_set__name", "id")

    def _calculate_filters(self, aphia_ids: list[int], request: Request) -> Q:  # noqa: PLR0912
        """Calculate the filters to apply to the Annotation queryset based on the query parameters.

        Args:
            aphia_ids (list[int]): List of AphiaIDs to filter the Annotations by.
            request (Request): The incoming HTTP request containing additional query parameters.

        Returns:
            Q: A Django Q object representing the filters to apply to the Annotation queryset.
        """
        name_part = request.query_params.get("name_part")
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

        map_fields = {
            "image_set_name": "annotation__image__image_set__name",
            "project": "annotation__image__image_set__project__name",
            "platform": "annotation__image__image_set__platform__name",
        }
        for param_name, db_field in map_fields.items():
            value = request.query_params.get(param_name)
            if value:
                value = value.strip()
                filters &= Q(**{f"{db_field}__icontains": value})

        exclude_aphia_ids = self._get_aphia_ids_from_query(request, "exclude_aphia_ids[]")
        if exclude_aphia_ids:
            filters &= ~Q(label__lowest_aphia_id__in=exclude_aphia_ids)

        exclude_annotation_sets = self._get_uuid_list_query_param(request, "exclude_annotation_set[]")
        if exclude_annotation_sets:
            filters &= ~Q(annotation__annotation_set__id__in=exclude_annotation_sets)

        exclude_image_sets = self._get_uuid_list_query_param(request, "exclude_image_set[]")
        if exclude_image_sets:
            filters &= ~Q(annotation__image__image_set__id__in=exclude_image_sets)

        filters = self._calculate_fields_filters(filters=filters, request=request)
        return filters

    def _calculate_fields_filters(self, filters: Q, request: Request) -> Q:
        """Calculate filters for the non-taxonomic fields based on the query parameters.

        Args:
            filters (Q): The existing filters to add to.
            request (Request): The incoming HTTP request containing additional query parameters.

        Returns:
            Q: A Django Q object representing the updated filters to apply to the Annotation queryset.
        """
        map_fields = {
            "deployment": "annotation__image__image_set__deployment",
            "fauna_attraction": "annotation__image__image_set__fauna_attraction",
            "marine_zone": "annotation__image__image_set__marine_zone",
        }
        for field_name, db_field in map_fields.items():
            value = request.query_params.get(field_name)
            if value:
                value = value.strip()
                filters &= Q(**{f"{db_field}": value})

        map_location_fields = {
            "min_lat": "annotation__image__latitude__gte",
            "max_lat": "annotation__image__latitude__lte",
            "min_lon": "annotation__image__longitude__gte",
            "max_lon": "annotation__image__longitude__lte",
        }
        for param_name, db_field in map_location_fields.items():
            value = self._get_float_query_param(request, param_name)
            if value is not None:
                filters &= Q(**{db_field: float(value)})
        return filters

    def _validate_search_params(self, request: Request) -> Response | None:  # noqa: PLR0912
        """Validate the search query parameters.

        Args:
            request (Request): The incoming HTTP request containing the query parameters.

        Returns:
            Response | None: A DRF Response object with an error message if validation
        fails, or None if validation passes.
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
        aphia_ids = self._get_aphia_ids_from_query(request, "aphia_ids[]")
        name_part = request.query_params.get("name_part")
        if not aphia_ids and not name_part:
            errors["query"] = "At least one of 'aphia_ids[]' or 'name_part' query parameters must be provided."
        length_limit_params = ["name_part", "project", "platform", "image_set_name"]
        for param_name in length_limit_params:
            value = request.query_params.get(param_name)
            if value and len(value.strip()) < MIN_CHARS_FOR_PARTIAL_MATCH:
                errors[param_name] = f"'{param_name}' must contain at least {MIN_CHARS_FOR_PARTIAL_MATCH} characters."

        errors = self._validate_bbox_params(request, errors)

        if errors:
            return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

        return None

    def _validate_bbox_params(self, request: Request, errors: dict) -> dict:
        """Validate the bounding box query parameters.

        Args:
            request (Request): The incoming HTTP request containing the query parameters.
            errors (dict): The current dictionary of validation errors to add to if any bbox parameters are invalid.

        Returns:
            dict: The updated dictionary of validation errors including any bbox parameter errors.
        """
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

        if min_lat is not None and not (-90 <= min_lat <= 90):  # noqa: PLR2004
            errors["min_lat"] = "'min_lat' must be between -90 and 90."
        if max_lat is not None and not (-90 <= max_lat <= 90):  # noqa: PLR2004
            errors["max_lat"] = "'max_lat' must be between -90 and 90."
        if min_lon is not None and not (-180 <= min_lon <= 180):  # noqa: PLR2004
            errors["min_lon"] = "'min_lon' must be between -180 and 180."
        if max_lon is not None and not (-180 <= max_lon <= 180):  # noqa: PLR2004
            errors["max_lon"] = "'max_lon' must be between -180 and 180."

        if min_lat is not None and max_lat is not None and min_lat > max_lat:
            errors["latitude_range"] = "'min_lat' must be less than or equal to 'max_lat'."
        if min_lon is not None and max_lon is not None and min_lon > max_lon:
            errors["longitude_range"] = "'min_lon' must be less than or equal to 'max_lon'."
        return errors

    def _get_all_aphia_ids_from_request(self, request: Request) -> dict | Response:
        """Extract and validate a list of AphiaIDs from the query parameters, including descendants if requested.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            dict | Response: A dictionary of valid AphiaIDs extracted from the query parameters or a Response in case of
        an error.
        """
        aphia_ids = self._get_aphia_ids_from_query(request, "aphia_ids[]")
        aphia_ids_info = _get_aphia_ids_info(aphia_ids)
        name_part = request.query_params.get("name_part")
        include_descendants = request.query_params.get("include_descendants", "false").lower() == "true"
        if name_part:
            name_part = name_part.strip()
            aphia_ids_info.update(_get_aphia_ids_by_name_part(name_part) or {})

        if not aphia_ids_info:
            return (
                Response(
                    {"detail": "No valid AphiaIDs found for the provided query parameters."},
                    status=status.HTTP_404_NOT_FOUND,
                )
                if not name_part
                else {}
            )

        if include_descendants:
            descendant_ids_info = _get_descendant_aphia_ids(aphia_ids) or {}
            aphia_ids_info.update(descendant_ids_info)

        return aphia_ids_info

    def _get_float_query_param(self, request: Request, name: str) -> float | None:
        """Extract a float query parameter."""
        value = request.query_params.get(name)
        if value in (None, ""):
            return None
        return float(value)

    def _get_aphia_ids_from_query(self, request: Request, name: str) -> list[int]:
        """Extract and validate a list of integer query parameter values."""
        raw_ids = request.query_params.getlist(name)
        aphia_ids = []
        for value in raw_ids:
            try:
                aphia_ids.append(int(value))
            except (TypeError, ValueError):
                continue
        return aphia_ids

    def _get_uuid_list_query_param(self, request: Request, name: str) -> list[uuid.UUID]:
        """Extract and validate a list of UUID query parameter values."""
        raw_ids = request.query_params.getlist(name)
        uuids = []
        for value in raw_ids:
            try:
                uuids.append(uuid.UUID(str(value)))
            except (TypeError, ValueError, AttributeError):
                continue
        return uuids

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

    def _build_info(self, queryset: QuerySet, aphia_ids_info: dict) -> dict:
        """Build unique image set, annotation set and Aphia ID info for search results.

        Args:
            queryset (QuerySet): The queryset to build the info for.
            aphia_ids_info (dict): A dictionary mapping AphiaIDs to their details.

        Returns:
            dict: A dictionary containing unique image set, annotation set and Aphia ID info.
        """
        image_sets = list(
            queryset.values(
                uuid=F("annotation__image__image_set__id"),
                name=F("annotation__image__image_set__name"),
            )
            .distinct()
            .order_by("name", "uuid")
        )
        annotation_sets = list(
            queryset.values(
                uuid=F("annotation__annotation_set__id"),
                name=F("annotation__annotation_set__name"),
            )
            .distinct()
            .order_by("name", "uuid")
        )
        return {
            "image_sets": image_sets,
            "annotation_sets": annotation_sets,
            "aphia_ids": aphia_ids_info.values(),
        }

    def _disable_pagination_requested(self, request: Request) -> bool:
        """Return whether pagination should be disabled for this request."""
        return request.query_params.get("disable_pagination", "false").lower() == "true"


def _get_descendant_aphia_ids(aphia_ids: list[int]) -> dict[dict]:
    """Get descendant AphiaIDs for a list of AphiaIDs.

    Args:
        aphia_ids (list[int]): List of AphiaIDs to get descendants for.

    Returns:
        dict[dict]: A dictionary mapping AphiaIDs to their details.
    """
    client = CachedWoRMSClient()
    return_dict = {}
    try:
        details_list = client.descendants_aphia_ids(aphia_ids) or []
    except requests.RequestException:
        return {}
    for detail in details_list:
        return_dict[detail["AphiaID"]] = {
            "aphia_id": detail["AphiaID"],
            "scientific_name": detail["scientificname"],
            "rank": detail["rank"],
        }
    return return_dict


def _get_aphia_ids_by_name_part(name_part: str) -> dict[dict]:
    """Get AphiaIDs for a given name part.

    Args:
        name_part (str): The name part to search for.

    Returns:
        dict[dict] | None: A dictionary mapping AphiaIDs to their details.
    """
    client = CachedWoRMSClient()
    return_dict = {}
    try:
        details_list = client.aphia_ids_by_name_part(name_part, combine_vernaculars=True, id_only=False) or []
    except requests.RequestException:
        return {}
    for detail in details_list:
        return_dict[detail["aphia_id"]] = {
            "aphia_id": detail["aphia_id"],
            "scientific_name": detail["scientific_name"],
            "rank": detail["rank"],
        }
    return return_dict


def _get_aphia_ids_info(aphia_ids: list[int]) -> dict[dict]:
    """Get aphia IDs and their details from the WoRMS API.

    Args:
        aphia_ids (list[int]): List of AphiaIDs to get scientific names for.

    Returns:
        dict[dict]: A dictionary mapping AphiaIDs to their details, including scientific names.
    """
    client = CachedWoRMSClient()
    return_dict = {}
    try:
        details_list = client.get_taxa(aphia_ids) or []
    except requests.RequestException:
        details_list = []
    for detail in details_list:
        return_dict[detail["AphiaID"]] = {
            "aphia_id": detail["AphiaID"],
            "scientific_name": detail["scientificname"],
            "rank": detail["rank"],
        }
    return return_dict
