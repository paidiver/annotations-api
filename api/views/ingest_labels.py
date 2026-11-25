"""View for ingesting label-set submission workbooks."""

import pandas as pd
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from api.serializers import FileUploadSerializer
from api.utils.labels_ingest import ingest_label_data
from api.utils.labels_parser import parse_label_set_metadata, parse_labels


@extend_schema(tags=["Ingest"])
class UploadLabelsView(viewsets.ViewSet):
    """Import a label set and its labels from an XLSX workbook."""

    parser_classes = [MultiPartParser, FormParser]
    serializer_class = FileUploadSerializer

    @extend_schema(
        tags=["Ingest"],
        summary="Import a label set from XLSX",
        operation_id="upload_labels",
        request=FileUploadSerializer,
        responses={
            201: inline_serializer(
                name="LabelSetIngestReport",
                fields={
                    "label_set_id": serializers.UUIDField(),
                    "label_count": serializers.IntegerField(),
                    "labels": serializers.ListField(child=serializers.DictField()),
                },
            )
        },
    )
    def create(self, request: Request) -> Response:
        """Receive an XLSX workbook and import its label data."""
        upload_serializer = FileUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)
        file = upload_serializer.validated_data["file"]

        if not file.name.lower().endswith(".xlsx"):
            raise serializers.ValidationError({"file": ["Provided file is not a .xlsx file."]})

        try:
            with pd.ExcelFile(file) as workbook:
                label_set_df = pd.read_excel(
                    workbook,
                    sheet_name="label-set-attributes",
                    header=None,
                )
                labels_df = pd.read_excel(
                    workbook,
                    sheet_name="label-attributes",
                    header=None,
                )
        except Exception as exc:
            raise serializers.ValidationError({"file": ["Failed to read Excel file."]}) from exc

        try:
            label_set_id, label_set_data = parse_label_set_metadata(label_set_df)
            labels_data = parse_labels(labels_df)
        except ValueError as exc:
            raise serializers.ValidationError({"file": [f"Error parsing label-set template: {exc}"]}) from exc

        result = ingest_label_data(
            label_set_id,
            label_set_data,
            labels_data,
        )

        return Response(
            {
                "label_set_id": result["label_set"]["id"],
                "label_count": len(result["labels"]),
                "labels": result["labels"],
            },
            status=HTTP_201_CREATED,
        )
