"""ViewSet for the ImageSet model."""

from django.db import transaction
from django.db.models import CharField, QuerySet
from django.db.models.functions import Cast
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from api.models import ImageSet
from api.serializers import ImageSetSerializer
from api.views.set_filters import filter_set_queryset

IMAGE_SET_FILTERS = {
    "name": "name",
    "project": "project__name",
    "context": "context__name",
    "abstract": "abstract",
    "objective": "objective",
    "target_timescale": "target_timescale",
    "handle": "handle",
    "platform": "platform__name",
    "sensor": "sensor__name",
}

IMAGE_SET_FILTER_PARAMETERS = [
    OpenApiParameter(
        name=name,
        type=str,
        description=f"Filter image sets by {name} (case-insensitive partial match).",
    )
    for name in IMAGE_SET_FILTERS
] + [
    OpenApiParameter(name="uuid", type=str, description="Filter by part of the image-set UUID."),
    OpenApiParameter(name="longitude", type=str, description="Filter by part of the longitude."),
    OpenApiParameter(name="latitude", type=str, description="Filter by part of the latitude."),
]


@extend_schema(tags=["Images API"])
class ImageSetViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageSet model."""

    queryset = ImageSet.objects.all().order_by("id")
    serializer_class = ImageSetSerializer

    @extend_schema(parameters=IMAGE_SET_FILTER_PARAMETERS)
    def list(self, request: Request, *args, **kwargs) -> Response:
        """List image sets, optionally filtered by their searchable metadata."""
        return super().list(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[ImageSet]:
        """Return image sets matching all supplied query parameters."""
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset

        queryset = filter_set_queryset(queryset, self.request, IMAGE_SET_FILTERS)
        for parameter in ("longitude", "latitude"):
            value = self.request.query_params.get(parameter, "").strip()
            if not value:
                continue
            text_alias = f"{parameter}_as_text"
            queryset = queryset.alias(**{text_alias: Cast(parameter, output_field=CharField())})
            queryset = queryset.filter(**{f"{text_alias}__icontains": value})

        return queryset

    @transaction.atomic
    def perform_create(self, serializer: ImageSetSerializer) -> None:
        """Override perform_create to handle nested creation of related objects.

        This method is wrapped in a transaction to ensure atomicity. If any part of the creation process fails (e.g.,
        creating related objects), the entire transaction will be rolled back, preventing partial data from being saved
        to the database.

        Args:
            serializer: The serializer instance with validated data.
        """
        serializer.save()

    @transaction.atomic
    def perform_update(self, serializer: ImageSetSerializer) -> None:
        """Override perform_update to handle nested updates of related objects.

        This method is wrapped in a transaction to ensure atomicity. If any part of the update process fails (e.g.,
        updating related objects), the entire transaction will be rolled back, preventing partial updates from being
        saved to the database.

        Args:
            serializer: The serializer instance with validated data.
        """
        serializer.save()
