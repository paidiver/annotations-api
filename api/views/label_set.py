"""ViewSet for the LabelSet model."""

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from api.models import LabelSet
from api.serializers import LabelSetSerializer
from api.views.set_filters import filter_set_queryset

LABEL_SET_FILTERS = {
    "name": "name",
    "project": "project__name",
    "context": "context__name",
    "abstract": "abstract",
    "objective": "objective",
    "handle": "handle",
}

LABEL_SET_FILTER_PARAMETERS = [
    OpenApiParameter(name=name, type=str, description=f"Filter label sets by {name} (case-insensitive partial match).")
    for name in LABEL_SET_FILTERS
] + [OpenApiParameter(name="uuid", type=str, description="Filter by an exact label-set UUID.")]


@extend_schema(tags=["Labels API"])
class LabelSetViewSet(viewsets.ModelViewSet):
    """ViewSet for the LabelSet model."""

    queryset = LabelSet.objects.all().order_by("id")
    serializer_class = LabelSetSerializer

    @extend_schema(parameters=LABEL_SET_FILTER_PARAMETERS)
    def list(self, request: Request, *args, **kwargs) -> Response:
        """List label sets, optionally filtered by their searchable metadata."""
        return super().list(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[LabelSet]:
        """Return label sets matching all supplied query parameters."""
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        return filter_set_queryset(queryset, self.request, LABEL_SET_FILTERS)
