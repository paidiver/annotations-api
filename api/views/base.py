"""API views module."""

import pandas as pd
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


EVENT_HEADER_KEYS = {
    "image-set-name",
    "image-project",
    "image-context",
    "image-abstract",
    "image-event",
    "image-platform",
    "image-sensor",
    "image-set-uuid",
    "image-set-handle",
    "image-set-ifdo-version",
    "image-creators",
    "image-pi",
    "image-license",
    "image-copyright",
    "image-coordinate-reference-system",
    "image-coordinate-uncertainty-meters",
    "image-longitude",
    "image-latitude",
    "image-altitude-meters",
    "image-acquisition",
    "image-quality",
    "image-deployment",
    "image-navigation",
    "image-scale-reference",
    "image-illumination",
    "image-pixel-magnitude",
    "image-marine-zone",
    "image-spectral-resolution",
    "image-capture-mode",
    "image-area-square-meter",
    "image-meters-above-ground",
    "image-acquisition-settings",
    "image-set-local-path",
    "image-datetime-format",
    "image-camera-housing-viewport",
    "image-flatport-parameters",
    "image-domeport-parameters",
    "image-camera-calibration-model",
    "image-photometric-calibration",
    "image-objective",
    "image-target-environment",
    "image-target-timescale",
    "image-spatial-constraints",
    "image-temporal-constraints",
    "image-time-synchronisation",
    "image-item-identification-scheme",
    "image-curation-protocol",
    "image-visual-constraints",
    "image-set-min-latitude-degrees",
    "image-set-max-latitude-degrees",
    "image-set-min-longitude-degrees",
    "image-set-max-longitude-degrees",
    "image-set-start-datetime",
    "image-set-end-datetime",
    "image-set-related-material",
    "image-set-provenance",
    "image-fauna-attraction",
}


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
        if not file.name.endswith(".xlsx"):
            return Response(
                {"error": "Provided file is not a .xlsx file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        df = pd.read_excel(file, sheet_name="Event header")

        # Iterate through each row to store values in a dict.
        event_header = {}
        for _, row in df.iterrows():
            key = str(row.iloc[0]).strip()
            value = row.iloc[1]

            if key in EVENT_HEADER_KEYS and pd.notna(value):
                event_header[key] = value

        print("Parsed Event header:")
        for k, v in event_header.items():
            print(f"{k}: {v}")

        print(df.head())

        return Response(
            {
                "status": "uploaded",
            },
            status=status.HTTP_201_CREATED,
        )
