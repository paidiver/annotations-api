"""API views module."""

import pandas as pd
from rest_framework import status
from rest_framework.request import Request
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
    def post(self, request: Request) -> Response:
        """Endpoint to receive an XLSX file and import it into the database.

        Args:
            request (Request): XLSX file to be imported.

        Returns:
            Response: JSON success/fail response.
        """
        file = request.FILES.get("file")
        print(file)

        # Exit if no file provided.
        if not file:
            return Response(
                {"error": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Exit if file not a XLSX (Excel) file.
        if not str(file).endswith(".xlsx"):
            return Response(
                {"error": "Provided file is not a .xlsx file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        df = pd.read_excel(file)

        print(df.head())

        return Response(
            {
                "filename": file.name,
                "content_type": file.content_type,
                "size": file.size,
                "status": "uploaded",
            },
            status=status.HTTP_201_CREATED,
        )
