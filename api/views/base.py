"""API views module."""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Health check view to verify service status."""

    def get(self, request):
        """Health check endpoint.

        Args:
            request: HTTP request object

        Returns:
            Response: JSON response indicating service status
        """
        return Response({"status": "ok"})


@extend_schema(tags=["Field Model API"])
class BaseFieldsViewSets(viewsets.ModelViewSet):
    """Base viewset for all field-related models."""

    pass


@extend_schema(tags=["Image Metadata API"])
class BaseImageMetadataViewSets(viewsets.ModelViewSet):
    """Base viewset for all image metadata-related models."""

    pass
