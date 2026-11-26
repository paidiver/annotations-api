"""ViewSet for the Annotation model."""

import pandas as pd
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from api.models import Annotation
from api.serializers import AnnotationSerializer, FileUploadSerializer
from api.utils.annotations_ingest import ingest_annotation_data
from api.utils.annotations_parser import (
    parse_annotation_data,
    parse_annotation_models,
    parse_annotation_set_metadata,
)


@extend_schema(tags=["Annotations API"])
class AnnotationViewSet(viewsets.ModelViewSet):
    """ViewSet for the Annotation model."""

    queryset = Annotation.objects.select_related("image").order_by("id")
    serializer_class = AnnotationSerializer


@extend_schema(tags=["Ingest"])
class UploadAnnotationsView(viewsets.ViewSet):
    """Import an annotation set from an XLSX workbook."""

    parser_classes = [MultiPartParser, FormParser]
    serializer_class = FileUploadSerializer

    @extend_schema(
        tags=["Ingest"],
        summary="Import an annotation set from XLSX",
        operation_id="upload_annotations",
        request=FileUploadSerializer,
        responses={
            201: inline_serializer(
                name="AnnotationIngestReport",
                fields={
                    "annotation_set_id": serializers.UUIDField(),
                    "model_count": serializers.IntegerField(),
                    "annotation_count": serializers.IntegerField(),
                    "models": serializers.ListField(child=serializers.DictField()),
                    "annotations": serializers.ListField(child=serializers.DictField()),
                },
            )
        },
    )
    def create(self, request: Request) -> Response:
        """Receive and ingest a v3 annotation workbook."""
        upload_serializer = FileUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)
        file = upload_serializer.validated_data["file"]

        if not file.name.lower().endswith(".xlsx"):
            raise serializers.ValidationError({"file": ["Provided file is not a .xlsx file."]})

        try:
            with pd.ExcelFile(file) as workbook:
                annotation_set_df = pd.read_excel(
                    workbook,
                    sheet_name="annotation-set-attributes",
                    header=None,
                )
                annotation_models_df = pd.read_excel(
                    workbook,
                    sheet_name="annotation-set-model-attributes",
                    header=None,
                )
                annotations_df = pd.read_excel(
                    workbook,
                    sheet_name="annotation-attributes",
                    header=None,
                )
        except Exception as exc:
            raise serializers.ValidationError({"file": ["Failed to read Excel file."]}) from exc

        try:
            (
                annotation_set_id,
                annotation_set_data,
                references,
            ) = parse_annotation_set_metadata(annotation_set_df)
            models_data = parse_annotation_models(annotation_models_df)
            annotations_data = parse_annotation_data(annotations_df)
        except ValueError as exc:
            raise serializers.ValidationError({"file": [f"Error parsing annotation template: {exc}"]}) from exc

        result = ingest_annotation_data(
            annotation_set_id,
            annotation_set_data,
            references,
            models_data,
            annotations_data,
        )

        return Response(
            {
                "annotation_set_id": result["annotation_set"]["id"],
                "model_count": len(result["models"]),
                "annotation_count": len(result["annotations"]),
                "models": result["models"],
                "annotations": result["annotations"],
            },
            status=HTTP_201_CREATED,
        )
