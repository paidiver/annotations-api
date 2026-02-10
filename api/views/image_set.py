"""ViewSet for the ImageSet model."""

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from api.models import ImageSet
from api.serializers import ImageSetSerializer


@extend_schema(tags=["Images API"])
class ImageSetViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageSet model."""

    queryset = ImageSet.objects.all().order_by("id")
    serializer_class = ImageSetSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        """Override perform_create to handle nested creation of related objects.

        This method is wrapped in a transaction to ensure atomicity. If any part of the creation process fails (e.g.,
        creating related objects), the entire transaction will be rolled back, preventing partial data from being saved
        to the database.

        Args:
            serializer: The serializer instance with validated data.
        """
        serializer.save()

    @transaction.atomic
    def perform_update(self, serializer):
        """Override perform_update to handle nested updates of related objects.

        This method is wrapped in a transaction to ensure atomicity. If any part of the update process fails (e.g.,
        updating related objects), the entire transaction will be rolled back, preventing partial updates from being
        saved to the database.

        Args:
            serializer: The serializer instance with validated data.
        """
        serializer.save()
