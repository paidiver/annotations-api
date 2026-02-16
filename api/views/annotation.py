"""ViewSet for the Annotation model."""

import pandas as pd
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from api.models import Annotation, AnnotationLabel, Annotator
from api.serializers import AnnotationLabelSerializer, AnnotationSerializer, AnnotatorSerializer, FileUploadSerializer
from api.utils.annotation import insert_annotations_into_tables
from api.utils.constants import ANNOTATION_KEYS


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

        # Exit if file not a XLSX (Excel) file.
        if not file.name.endswith(".xlsx"):
            return Response(
                {"error": "Provided file is not a .xlsx file."},
                status=HTTP_400_BAD_REQUEST,
            )

        try:
            df = pd.read_excel(file, sheet_name="Annotation set metadata")
        except Exception:
            return Response(
                {"error": "Failed to read Excel file."},
                status=HTTP_400_BAD_REQUEST,
            )

        df = df.iloc[:, :3]
        df.iloc[:, 2] = df.iloc[:, 2].fillna("")

        annotation_data = {}
        current_main_key = None

        for main_key, sub_key, value in df.itertuples(index=False, name=None):
            # Update main key if valid
            if pd.notna(main_key) and str(main_key).strip():
                current_main_key = str(main_key).strip()

            # Skip if no main key yet
            if not current_main_key:
                continue

            sub_key_clean = str(sub_key).strip() if pd.notna(sub_key) else ""

            final_key = f"{current_main_key}-{sub_key_clean}" if sub_key_clean else current_main_key

            # Store only if value exists
            if pd.notna(value) and final_key in ANNOTATION_KEYS:
                annotation_data[final_key] = value

        insert_annotations_into_tables(data=annotation_data)

        return Response(
            {"status": "uploaded", "data": annotation_data},
            status=HTTP_201_CREATED,
        )
