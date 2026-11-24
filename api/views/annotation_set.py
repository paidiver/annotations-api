"""ViewSet for the AnnotationSet model."""

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from api.models import AnnotationSet, AnnotationSetModel
from api.serializers import AnnotationSetModelSerializer, AnnotationSetSerializer
from api.views.set_filters import filter_set_queryset

ANNOTATION_SET_FILTERS = {
    "name": "name",
    "project": "project__name",
    "context": "context__name",
    "abstract": "abstract",
    "objective": "objective",
    "target_environment": "target_environment",
    "handle": "handle",
    "obis_data": "obis_handles",
    "target_timescale": "target_timescale",
    "label-name": "label_sets__labels__name",
}

ANNOTATION_SET_FILTER_PARAMETERS = [
    OpenApiParameter(
        name=name,
        type=str,
        description=f"Filter annotation sets by {name} (case-insensitive partial match).",
    )
    for name in ANNOTATION_SET_FILTERS
] + [OpenApiParameter(name="uuid", type=str, description="Filter by part of the annotation-set UUID.")]


@extend_schema(tags=["Annotations API"])
class AnnotationSetViewSet(viewsets.ModelViewSet):
    """ViewSet for the AnnotationSet model."""

    queryset = AnnotationSet.objects.all().order_by("id")
    serializer_class = AnnotationSetSerializer

    @extend_schema(parameters=ANNOTATION_SET_FILTER_PARAMETERS)
    def list(self, request: Request, *args, **kwargs) -> Response:
        """List annotation sets, optionally filtered by their searchable metadata."""
        return super().list(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[AnnotationSet]:
        """Return annotation sets matching all supplied query parameters."""
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        queryset = filter_set_queryset(queryset, self.request, ANNOTATION_SET_FILTERS)
        if self.request.query_params.get("label-name", "").strip():
            queryset = queryset.distinct()
        return queryset


@extend_schema(tags=["Annotations API"])
class AnnotationSetModelViewSet(viewsets.ModelViewSet):
    """ViewSet for the AnnotationSetModel model."""

    queryset = AnnotationSetModel.objects.all().order_by("id")
    serializer_class = AnnotationSetModelSerializer
