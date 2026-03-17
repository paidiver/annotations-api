"""ViewSet for the Annotation model."""

from drf_spectacular.utils import extend_schema
import requests
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from api.models import Annotation
from api.serializers import AnnotationSerializer
from django.conf import settings
import requests


@extend_schema(tags=["Annotations API"])
class AnnotationSearchViewSet(viewsets.ModelViewSet):
    """ViewSet for searching Annotations."""

    def get(self, request: Request, *args, **kwargs):
        aphia_ids = request.query_params.get("aphia_ids", "").split(",")
        name_part = request.query_params.get("name_part")
        include_descendants = request.query_params.get("include_descendants", "false").lower() == "true"
        if not aphia_ids and not name_part:
            return Response({"detail": "Please provide either 'aphia_ids' or 'name_part' query parameter."}, status=400)
        if name_part:
            aphia_ids.extend(_get_aphia_ids_by_name_part(name_part))

        else:
            return Response({"detail": "Please provide either 'aphia_id' or 'name_part' query parameter."}, status=400)


def _get_aphia_ids_by_name_part(name_part: str):
    response = requests.get(
        f"{settings.CACHED_WORMS_API_BASE_URL}/taxa/ajax_by_name_part/{name_part}/?combine_vernaculars=true"
    )
    if response.status_code == 200:
        data = response.json()
        return [item["AphiaID"] for item in data]
    else:
        return []
