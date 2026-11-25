"""Tests for the annotation-set XLSX ingestion endpoint."""

from unittest import SkipTest

from django.conf import settings

if not settings.ENABLE_ANNOTATION_INGEST:
    raise SkipTest("Annotation ingest is disabled")

import io
from unittest.mock import Mock, patch
from uuid import UUID

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import serializers, status

from api.tests.utils.auth_utils import AuthenticatedAPITestCase


class UploadAnnotationsViewTests(AuthenticatedAPITestCase):
    """Tests for the annotation-set XLSX ingestion endpoint."""

    def setUp(self) -> None:
        """Set up common test data."""
        super().setUp()

        self.upload_url = reverse("ingest-annotation-sets")

        self.annotation_set_id = UUID("00000000-0000-0000-0000-000000000001")
        self.annotation_id = UUID("00000000-0000-0000-0000-000000000002")

        self.annotation_set_data = {
            "name": "Test annotation set",
        }
        self.references = {
            "image_set_names": ["Test image set"],
            "image_set_ids": [],
            "image_set_handles": [],
            "label_set_names": ["Test label set"],
            "label_set_ids": [UUID("00000000-0000-0000-0000-000000000003")],
        }
        self.models_data = [
            {
                "model_id": "test-model",
                "name": "Test model",
            }
        ]
        self.annotations_data = [
            {
                "id": self.annotation_id,
                "image_filename": "test-image.jpg",
            }
        ]

    @staticmethod
    def create_mock_xlsx_file() -> SimpleUploadedFile:
        """Create a workbook containing all required v3 worksheets."""
        file_stream = io.BytesIO()

        worksheets = {
            "annotation-set-attributes": pd.DataFrame(
                [
                    ["annotation-set-name", "Test annotation set"],
                ]
            ),
            "annotation-set-model-attributes": pd.DataFrame(
                [
                    ["annotation-model-id", "test-model"],
                ]
            ),
            "annotation-attributes": pd.DataFrame(
                [
                    ["annotation-uuid", "image-filename"],
                    [
                        "00000000-0000-0000-0000-000000000002",
                        "test-image.jpg",
                    ],
                ]
            ),
        }

        with pd.ExcelWriter(file_stream, engine="openpyxl") as writer:
            for sheet_name, dataframe in worksheets.items():
                dataframe.to_excel(
                    writer,
                    index=False,
                    header=False,
                    sheet_name=sheet_name,
                )

        file_stream.seek(0)

        return SimpleUploadedFile(
            "test-annotations.xlsx",
            file_stream.getvalue(),
            content_type=("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"),
        )

    def mock_ingest_result(self) -> dict:
        """Return a representative successful ingestion result."""
        return {
            "annotation_set": {
                "id": str(self.annotation_set_id),
                "name": "Test annotation set",
            },
            "models": [
                {
                    "model_id": "test-model",
                    "name": "Test model",
                }
            ],
            "annotations": [
                {
                    "id": str(self.annotation_id),
                    "image_filename": "test-image.jpg",
                }
            ],
        }

    @patch("api.views.annotation.parse_annotation_set_metadata")
    @patch("api.views.annotation.parse_annotation_models")
    @patch("api.views.annotation.parse_annotation_data")
    @patch("api.views.annotation.ingest_annotation_data")
    def test_returns_201_for_valid_workbook(
        self,
        mock_ingest: Mock,
        mock_parse_annotations: Mock,
        mock_parse_models: Mock,
        mock_parse_annotation_set: Mock,
    ) -> None:
        """Ingest a valid v3 annotation workbook."""
        mock_parse_annotation_set.return_value = (
            self.annotation_set_id,
            self.annotation_set_data,
            self.references,
        )
        mock_parse_models.return_value = self.models_data
        mock_parse_annotations.return_value = self.annotations_data
        mock_ingest.return_value = self.mock_ingest_result()

        response = self.client.post(
            self.upload_url,
            {"file": self.create_mock_xlsx_file()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["annotation_set_id"],
            str(self.annotation_set_id),
        )
        self.assertEqual(response.data["model_count"], 1)
        self.assertEqual(response.data["annotation_count"], 1)
        self.assertEqual(
            response.data["models"],
            mock_ingest.return_value["models"],
        )
        self.assertEqual(
            response.data["annotations"],
            mock_ingest.return_value["annotations"],
        )

    @patch("api.views.annotation.parse_annotation_set_metadata")
    @patch("api.views.annotation.parse_annotation_models")
    @patch("api.views.annotation.parse_annotation_data")
    @patch("api.views.annotation.ingest_annotation_data")
    def test_parses_all_worksheets_and_calls_ingest(
        self,
        mock_ingest: Mock,
        mock_parse_annotations: Mock,
        mock_parse_models: Mock,
        mock_parse_annotation_set: Mock,
    ) -> None:
        """Pass each worksheet and all parsed data to the ingest service."""
        mock_parse_annotation_set.return_value = (
            self.annotation_set_id,
            self.annotation_set_data,
            self.references,
        )
        mock_parse_models.return_value = self.models_data
        mock_parse_annotations.return_value = self.annotations_data
        mock_ingest.return_value = self.mock_ingest_result()

        response = self.client.post(
            self.upload_url,
            {"file": self.create_mock_xlsx_file()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_parse_annotation_set.assert_called_once()
        mock_parse_models.assert_called_once()
        mock_parse_annotations.assert_called_once()

        annotation_set_dataframe = mock_parse_annotation_set.call_args.args[0]
        models_dataframe = mock_parse_models.call_args.args[0]
        annotations_dataframe = mock_parse_annotations.call_args.args[0]

        self.assertEqual(
            annotation_set_dataframe.iloc[0, 0],
            "annotation-set-name",
        )
        self.assertEqual(
            models_dataframe.iloc[0, 0],
            "annotation-model-id",
        )
        self.assertEqual(
            annotations_dataframe.iloc[0, 0],
            "annotation-uuid",
        )

        mock_ingest.assert_called_once_with(
            self.annotation_set_id,
            self.annotation_set_data,
            self.references,
            self.models_data,
            self.annotations_data,
        )

    def test_requires_file(self) -> None:
        """Reject a request that does not contain a file."""
        response = self.client.post(
            self.upload_url,
            {},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("No file was submitted.", str(response.data))

    def test_rejects_non_xlsx_file(self) -> None:
        """Reject an upload whose filename does not end in XLSX."""
        text_file = SimpleUploadedFile(
            "annotations.txt",
            b"Not an Excel workbook",
            content_type="text/plain",
        )

        response = self.client.post(
            self.upload_url,
            {"file": text_file},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "Provided file is not a .xlsx file.",
            str(response.data),
        )

    def test_rejects_invalid_excel_file(self) -> None:
        """Reject invalid content disguised as an XLSX file."""
        invalid_file = SimpleUploadedFile(
            "annotations.xlsx",
            b"Not a valid Excel workbook",
            content_type=("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"),
        )

        response = self.client.post(
            self.upload_url,
            {"file": invalid_file},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "Failed to read Excel file.",
            str(response.data),
        )

    def test_rejects_workbook_with_missing_worksheet(self) -> None:
        """Reject a workbook missing one of the required worksheets."""
        file_stream = io.BytesIO()

        with pd.ExcelWriter(file_stream, engine="openpyxl") as writer:
            pd.DataFrame([["annotation-set-name", "Test set"]]).to_excel(
                writer,
                index=False,
                header=False,
                sheet_name="annotation-set-attributes",
            )

        file_stream.seek(0)

        incomplete_file = SimpleUploadedFile(
            "incomplete.xlsx",
            file_stream.getvalue(),
            content_type=("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"),
        )

        response = self.client.post(
            self.upload_url,
            {"file": incomplete_file},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "Failed to read Excel file.",
            str(response.data),
        )

    @patch("api.views.annotation.parse_annotation_set_metadata")
    def test_returns_400_when_parsing_fails(
        self,
        mock_parse_annotation_set: Mock,
    ) -> None:
        """Convert parser ValueErrors into validation responses."""
        mock_parse_annotation_set.side_effect = ValueError("Missing required metadata: Annotation Set Name")

        response = self.client.post(
            self.upload_url,
            {"file": self.create_mock_xlsx_file()},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            ("Error parsing annotation template: " "Missing required metadata: Annotation Set Name"),
            str(response.data),
        )

    @patch("api.views.annotation.parse_annotation_set_metadata")
    @patch("api.views.annotation.parse_annotation_models")
    @patch("api.views.annotation.parse_annotation_data")
    @patch("api.views.annotation.ingest_annotation_data")
    def test_returns_400_when_ingestion_validation_fails(
        self,
        mock_ingest: Mock,
        mock_parse_annotations: Mock,
        mock_parse_models: Mock,
        mock_parse_annotation_set: Mock,
    ) -> None:
        """Propagate ingestion validation errors as HTTP 400."""
        mock_parse_annotation_set.return_value = (
            self.annotation_set_id,
            self.annotation_set_data,
            self.references,
        )
        mock_parse_models.return_value = self.models_data
        mock_parse_annotations.return_value = self.annotations_data
        mock_ingest.side_effect = serializers.ValidationError(
            {
                "image": [
                    "Image could not be resolved.",
                ]
            }
        )

        response = self.client.post(
            self.upload_url,
            {"file": self.create_mock_xlsx_file()},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "Image could not be resolved.",
            str(response.data),
        )
