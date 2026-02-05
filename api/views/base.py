"""API views module."""

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

class AnnotationsView(APIView):
    """Annotations view to import image annotation data into the database."""
    def get(self, request):
        return Response({"status": "of course!"})
