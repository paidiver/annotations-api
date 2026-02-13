"""ViewSet for the Annotation model."""

import pandas as pd
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from api.models import Annotation, AnnotationLabel, Annotator
from api.serializers import AnnotationLabelSerializer, AnnotationSerializer, AnnotatorSerializer, FileUploadSerializer

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


@extend_schema(tags=["Annotations API"])
class AnnotatorViewSet(viewsets.ModelViewSet):
    """ViewSet for the Annotator model."""

    queryset = Annotator.objects.all()
    serializer_class = AnnotatorSerializer


@extend_schema(tags=["Annotations API"])
class AnnotationViewSet(viewsets.ModelViewSet):
    """ViewSet for the Annotation model."""

    queryset = Annotation.objects.all().order_by("id")
    serializer_class = AnnotationSerializer


@extend_schema(tags=["Annotations API"])
class AnnotationLabelViewSet(viewsets.ModelViewSet):
    """ViewSet for the AnnotationLabel model."""

    queryset = AnnotationLabel.objects.all().order_by("id")
    serializer_class = AnnotationLabelSerializer


@extend_schema(tags=["Annotations API"])
class UploadAnnotationsView(viewsets.ViewSet):
    """Annotations view to import image annotation data into the database."""

    parser_classes = [MultiPartParser, FormParser]
    serializer_class = FileUploadSerializer

    def create(self, request: Request) -> Response:
        """Endpoint to receive an XLSX file and import it into the database.

        Args:
            request (Request): XLSX file to be imported.

        Returns:
            Response: JSON success/fail response.
        """
        serializer = FileUploadSerializer(data=request.data)
        # file = request.FILES.get("file")
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["file"]
        print(file)

        # Exit if file not a XLSX (Excel) file.
        if not file.name.endswith(".xlsx"):
            return Response(
                {"error": "Provided file is not a .xlsx file."},
                status=HTTP_400_BAD_REQUEST,
            )

        try:
            df = pd.read_excel(file, sheet_name="Event header")
        except Exception:
            return Response(
                {"error": "Failed to read Excel file."},
                status=HTTP_400_BAD_REQUEST,
            )

        # Iterate through each row to store values in a dict.
        event_header = {}
        for _, row in df.iterrows():
            if row.empty or pd.isna(row.iloc[0]):
                continue

            key = str(row.iloc[0]).strip()
            value = row.iloc[1]

            if key in EVENT_HEADER_KEYS and pd.notna(value):
                event_header[key] = value

        print("Parsed Event header:")
        for k, v in event_header.items():
            print(f"{k}: {v}")

        return Response(
            {"status": "uploaded"},
            status=HTTP_201_CREATED,
        )
