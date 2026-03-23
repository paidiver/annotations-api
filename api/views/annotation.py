"""ViewSet for the Annotation model."""

import pandas as pd
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from api.models import Annotation, AnnotationLabel, Annotator
from api.serializers import AnnotationLabelSerializer, AnnotationSerializer, AnnotatorSerializer, FileUploadSerializer
from api.utils.annotations_ingest import ingest_annotation_data
from api.utils.annotations_parser import (
    parse_annotation_data,
    parse_annotation_set_metadata,
    parse_label_set,
)


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


class UploadAnnotationsView(viewsets.ViewSet):
    """Annotations view to import image annotation data into the database."""

    parser_classes = [MultiPartParser, FormParser]
    serializer_class = FileUploadSerializer

    @extend_schema(
        tags=["Annotations API"],
        operation_id="upload_annotations",
        request=FileUploadSerializer,
        responses={201: OpenApiTypes.OBJECT},
    )
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
            label_df = pd.read_excel(file, sheet_name="Label set")
            annotaion_data = pd.read_excel(file, sheet_name="Annotation data")
        except Exception:
            return Response(
                {"error": "Failed to read Excel file."},
                status=HTTP_400_BAD_REQUEST,
            )

        annotation_set = parse_annotation_set_metadata(df)

        label_data = parse_label_set(label_df)

        annotation_data = parse_annotation_data(annotaion_data)

        data = ingest_annotation_data(annotation_set, label_data, annotation_data)
        return Response(
            {"status": "uploaded", "data": data},
            status=HTTP_201_CREATED,
        )
