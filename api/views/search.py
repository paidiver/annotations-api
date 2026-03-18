"""ViewSet for the Annotation model."""

import requests
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from api.models.annotation import Annotation
from api.serializers.annotation import AnnotationSerializer


@extend_schema(tags=["Annotations API"])
class AnnotationSearchViewSet(viewsets.ModelViewSet):
    """ViewSet for searching Annotations."""

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Search for Annotations based on query parameters.

        Args:
            request (Request): The incoming HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A DRF Response object containing the search results.
        """
        aphia_ids = request.query_params.get("aphia_ids", "").split(",")
        name_part = request.query_params.get("name_part")
        include_descendants = request.query_params.get("include_descendants", "false").lower() == "true"
        grouped = request.query_params.get("grouped", "false").lower() == "true"
        if not aphia_ids and not name_part:
            return Response(
                {"detail": "Please provide either 'aphia_ids' or 'name_part' query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if name_part:
            aphia_ids.extend(_get_aphia_ids_by_name_part(name_part))
        if include_descendants:
            all_aphia_ids = set(aphia_ids)
            descendants = _get_descendant_aphia_ids(aphia_ids)
            all_aphia_ids.update(descendants)
            aphia_ids = list(all_aphia_ids)

        annotations = Annotation.objects.filter(aphia_id__in=aphia_ids)
        if grouped:
            grouped_annotations = {}
            for annotation in annotations:
                aphia_id = annotation.aphia_id
                if aphia_id not in grouped_annotations:
                    grouped_annotations[aphia_id] = []
                grouped_annotations[aphia_id].append(annotation)
            return Response(grouped_annotations)
        else:
            serializer = AnnotationSerializer(annotations, many=True)
            return Response(serializer.data)


def _get_descendant_aphia_ids(aphia_ids: list[str]) -> list[str]:
    """Get descendant AphiaIDs for a list of AphiaIDs.

    Args:
        aphia_ids (list[str]): List of AphiaIDs to get descendants for.

    Returns:
        list[str]: List of descendant AphiaIDs.
    """
    response = requests.get(
        f"{settings.CACHED_WORMS_API_BASE_URL}/taxa/just_aphia_ids/?aphia_ids={','.join(aphia_ids)}&include_descendants=true"
    )
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        return [item["AphiaID"] for item in data]
    else:
        return []


def _get_aphia_ids_by_name_part(name_part: str) -> list[str]:
    """Get AphiaIDs for a given name part.

    Args:
        name_part (str): The name part to search for.

    Returns:
        list[str]: List of AphiaIDs matching the name part.
    """
    response = requests.get(
        f"{settings.CACHED_WORMS_API_BASE_URL}/taxa/ajax_by_name_part/{name_part}/just_aphia_ids/?combine_vernaculars=true"
    )
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        return [item["AphiaID"] for item in data]
    else:
        return []
