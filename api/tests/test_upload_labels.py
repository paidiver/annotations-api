"""Tests for the label-set XLSX ingestion endpoint."""

import io
from unittest.mock import Mock, patch
from uuid import UUID

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import serializers, status
from rest_framework.response import Response

from api.tests.utils.auth_utils import AuthenticatedAPITestCase

LABEL_SET_ID = UUID("e90a8bd7-5706-4ee0-bc9a-f36e5caf8216")


class UploadLabelsViewTests(AuthenticatedAPITestCase):
    """Tests for UploadLabelsView."""

    def setUp(self) -> None:
        """Set up common endpoint test data."""
        super().setUp()
        self.upload_url = reverse("ingest-label-sets")
        self.mock_file = self.create_mock_xlsx_file()
        self.label_set_data = {"name": "Test label set"}
        self.labels_data = [{"id": None, "name": "Test label"}]

    def create_mock_xlsx_file(self) -> SimpleUploadedFile:
        """Create an XLSX file containing the required worksheet names."""
        file_stream = io.BytesIO()

        label_set_df = pd.DataFrame(
            [
                ["Attribute name", "Value"],
                ["label-set-name", "Test label set"],
            ]
        )
        labels_df = pd.DataFrame(
            [
                ["Attribute name", "label-name"],
                ["Allowed value(s)", "Text"],
                ["Description", "Label name"],
                ["Updated requirement", "Required"],
                ["", "Test label"],
            ]
        )

        with pd.ExcelWriter(file_stream, engine="openpyxl") as writer:
            label_set_df.to_excel(
                writer,
                index=False,
                header=False,
                sheet_name="label-set-attributes",
            )
            labels_df.to_excel(
                writer,
                index=False,
                header=False,
                sheet_name="label-attributes",
            )

        file_stream.seek(0)

        return SimpleUploadedFile(
            "test_labels.xlsx",
            file_stream.getvalue(),
            content_type=("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"),
        )

    def assert_problem_error(
        self,
        response: Response,
        field: str,
        message: str,
    ) -> None:
        """Assert an RFC 9457 validation response contains an error."""
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.data["detail"],
            "One or more request parameters are invalid.",
        )

        errors = [(error["field"], error["message"]) for error in response.data["errors"]]
        self.assertIn((field, message), errors)

    @patch("api.views.ingest_labels.ingest_label_data")
    @patch("api.views.ingest_labels.parse_labels")
    @patch("api.views.ingest_labels.parse_label_set_metadata")
    def test_upload_labels_returns_201_for_valid_workbook(
        self,
        mock_parse_label_set: Mock,
        mock_parse_labels: Mock,
        mock_ingest: Mock,
    ) -> None:
        """Import a valid label workbook."""
        mock_parse_label_set.return_value = (
            LABEL_SET_ID,
            self.label_set_data,
        )
        mock_parse_labels.return_value = self.labels_data
        mock_ingest.return_value = {
            "label_set": {
                "id": str(LABEL_SET_ID),
                "name": "Test label set",
            },
            "labels": [
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "name": "Test label",
                }
            ],
        }

        response = self.client.post(
            self.upload_url,
            {"file": self.mock_file},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            response.data["label_set_id"],
            str(LABEL_SET_ID),
        )
        self.assertEqual(response.data["label_count"], 1)
        self.assertEqual(len(response.data["labels"]), 1)

        label_set_df = mock_parse_label_set.call_args.args[0]
        labels_df = mock_parse_labels.call_args.args[0]

        # header=None must preserve the workbook's first row.
        self.assertEqual(
            label_set_df.iloc[0, 0],
            "Attribute name",
        )
        self.assertEqual(
            labels_df.iloc[0, 0],
            "Attribute name",
        )

        mock_ingest.assert_called_once_with(
            LABEL_SET_ID,
            self.label_set_data,
            self.labels_data,
        )

    def test_upload_labels_rejects_non_xlsx_file(self) -> None:
        """Reject files that do not have an XLSX extension."""
        upload = SimpleUploadedFile(
            "labels.csv",
            b"not an xlsx file",
            content_type="text/csv",
        )

        response = self.client.post(
            self.upload_url,
            {"file": upload},
            format="multipart",
        )

        self.assert_problem_error(
            response,
            "file",
            "Provided file is not a .xlsx file.",
        )

    def test_upload_labels_rejects_invalid_excel_file(self) -> None:
        """Reject invalid XLSX content."""
        upload = SimpleUploadedFile(
            "labels.xlsx",
            b"not an Excel workbook",
            content_type=("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"),
        )

        response = self.client.post(
            self.upload_url,
            {"file": upload},
            format="multipart",
        )

        self.assert_problem_error(
            response,
            "file",
            "Failed to read Excel file.",
        )

    def test_upload_labels_rejects_missing_sheets(self) -> None:
        """Reject workbooks without the required worksheets."""
        file_stream = io.BytesIO()

        with pd.ExcelWriter(file_stream, engine="openpyxl") as writer:
            pd.DataFrame([["wrong sheet"]]).to_excel(
                writer,
                index=False,
                header=False,
                sheet_name="Wrong Sheet",
            )

        file_stream.seek(0)
        upload = SimpleUploadedFile(
            "labels.xlsx",
            file_stream.getvalue(),
            content_type=("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"),
        )

        response = self.client.post(
            self.upload_url,
            {"file": upload},
            format="multipart",
        )

        self.assert_problem_error(
            response,
            "file",
            "Failed to read Excel file.",
        )

    @patch("api.views.ingest_labels.parse_label_set_metadata")
    def test_upload_labels_returns_400_when_parsing_fails(
        self,
        mock_parse_label_set: Mock,
    ) -> None:
        """Return a validation response when workbook parsing fails."""
        mock_parse_label_set.side_effect = ValueError("label-set-name is required")

        response = self.client.post(
            self.upload_url,
            {"file": self.mock_file},
            format="multipart",
        )

        self.assert_problem_error(
            response,
            "file",
            ("Error parsing label-set template: " "label-set-name is required"),
        )

    @patch("api.views.ingest_labels.ingest_label_data")
    @patch("api.views.ingest_labels.parse_labels")
    @patch("api.views.ingest_labels.parse_label_set_metadata")
    def test_upload_labels_returns_400_when_ingestion_fails(
        self,
        mock_parse_label_set: Mock,
        mock_parse_labels: Mock,
        mock_ingest: Mock,
    ) -> None:
        """Return serializer validation errors from ingestion."""
        mock_parse_label_set.return_value = (
            LABEL_SET_ID,
            self.label_set_data,
        )
        mock_parse_labels.return_value = self.labels_data
        mock_ingest.side_effect = serializers.ValidationError(
            {"label-set-uuid": ["A label set with this UUID already exists."]}
        )

        response = self.client.post(
            self.upload_url,
            {"file": self.mock_file},
            format="multipart",
        )

        self.assert_problem_error(
            response,
            "label-set-uuid",
            "A label set with this UUID already exists.",
        )

    def test_upload_labels_requires_file(self) -> None:
        """Require the multipart file field."""
        response = self.client.post(
            self.upload_url,
            {},
            format="multipart",
        )

        self.assert_problem_error(
            response,
            "file",
            "No file was submitted.",
        )
