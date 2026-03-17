"""ViewSet for the Annotation model."""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from api.models import Annotation
from api.serializers import AnnotationSerializer


@extend_schema(tags=["Annotations API"])
class AnnotationSearchViewSet(viewsets.ModelViewSet):
    """ViewSet for searching Annotations."""

    def get(self, request: Request, *args, **kwargs):
        aphia_ids = request.query_params.get("aphia_ids", "").split(",")
        name_part = request.query_params.get("name_part")
        if not aphia_ids and not name_part:
            return Response({"detail": "Please provide either 'aphia_ids' or 'name_part' query parameter."}, status=400)
        if name_part:
            https://worms-cache.paidiver.site/api/taxa/ajax_by_name_part/spon/?combine_vernaculars=true
        if aphia_ids:
            aphia_ids_list = aphia_ids.split(",")
            annotations = Annotation.objects.filter(aphia_id__in=aphia_ids_list)
        elif name_part:
            annotations = Annotation.objects.filter(name__icontains=name_part)
        else:
            return Response({"detail": "Please provide either 'aphia_id' or 'name_part' query parameter."}, status=400)
