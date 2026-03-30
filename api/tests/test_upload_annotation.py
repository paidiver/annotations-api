"""Tests for UploadAnnotationsView."""

import io
from unittest.mock import Mock, patch

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from api.tests.utils.auth_utils import AuthenticatedAPITestCase


class UploadAnnotationsViewTests(AuthenticatedAPITestCase):
    """Tests for UploadAnnotationsView endpoints."""

    def setUp(self) -> None:
        """Set up test data and common variables."""
        super().setUp()
        self.upload_url = reverse("upload_annotation-list")
        self.mock_annotation_set = {"name": "Test Annotation Set"}
        self.mock_label_data = [{"name": "Label1", "parent": "Parent1"}]
        self.mock_annotation_data = [{"annotation": "data"}]
        self.mock_xlsx_file = self.create_mock_xlsx_file()

    def create_mock_xlsx_file(self) -> SimpleUploadedFile:
        """Create a mock XLSX file for testing."""
        file_stream = io.BytesIO()

        data = {
            "Annotation set metadata": pd.DataFrame([{"name": "Test Set", "description": "Test"}]),
            "Label set": pd.DataFrame([{"name": "Label1", "parent": "Parent1"}]),
            "Annotation data": pd.DataFrame([{"annotation_id": 1, "label": "Label1"}]),
        }

        with pd.ExcelWriter(file_stream, engine="openpyxl") as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, index=False, sheet_name=sheet_name)

        file_stream.seek(0)
        return SimpleUploadedFile(
            "test_annotations.xlsx",
            file_stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @patch("api.views.annotation.parse_annotation_set_metadata")
    @patch("api.views.annotation.parse_label_set")
    @patch("api.views.annotation.parse_annotation_data")
    @patch("api.views.annotation.ingest_annotation_data")
    def test_upload_annotations_returns_201_resp_for_valid_xlsx_file(
        self, mock_ingest: Mock, mock_parse_annotation: Mock, mock_parse_label: Mock, mock_parse_set: Mock
    ) -> None:
        """Test successful upload of a valid XLSX file."""
        mock_parse_set.return_value = self.mock_annotation_set
        mock_parse_label.return_value = self.mock_label_data
        mock_parse_annotation.return_value = self.mock_annotation_data
        mock_ingest.return_value = {"status": "success", "count": 10}

        xlsx_file = self.mock_xlsx_file
        response = self.client.post(
            self.upload_url,
            {"file": xlsx_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "uploaded")
        self.assertEqual(response.data["data"]["status"], "success")
        self.assertEqual(response.data["data"]["count"], 10)

    def test_upload_annotations_rejects_non_xlsx_file(self) -> None:
        """Test that uploading a non-.xlsx file is rejected."""
        text_file = SimpleUploadedFile("test_file.txt", b"This is not an Excel file", content_type="text/plain")

        response = self.client.post(self.upload_url, {"file": text_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Provided file is not a .xlsx file.")

    def test_upload_annotations_rejects_invalid_excel_file(self) -> None:
        """Test that uploading an invalid Excel file is rejected."""
        # This has the right name, but the content will make pd.read_excel fail
        invalid_file = SimpleUploadedFile(
            "invalid.xlsx",
            b"Not a valid Excel file content",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        response = self.client.post(
            self.upload_url,
            {"file": invalid_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Failed to read Excel file.")

    def test_upload_annotations_handles_missing_sheets(self) -> None:
        """Test that uploading a file with missing required sheets is rejected."""
        file_stream = io.BytesIO()
        df = pd.DataFrame([{"name": "wrong sheet"}])
        with pd.ExcelWriter(file_stream, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Wrong Sheet")
        file_stream.seek(0)
        file_stream.name = "incomplete.xlsx"

        response = self.client.post(
            self.upload_url,
            {"file": file_stream},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("api.views.annotation.parse_annotation_set_metadata")
    @patch("api.views.annotation.parse_label_set")
    @patch("api.views.annotation.parse_annotation_data")
    @patch("api.views.annotation.ingest_annotation_data")
    def test_upload_annotations_calls_parse_functions_correctly(
        self, mock_ingest: Mock, mock_parse_annotation: Mock, mock_parse_label: Mock, mock_parse_set: Mock
    ) -> None:
        """Test that the correct parse functions are called with the correct data."""
        mock_parse_set.return_value = self.mock_annotation_set
        mock_parse_label.return_value = self.mock_label_data
        mock_parse_annotation.return_value = self.mock_annotation_data
        mock_ingest.return_value = {}

        xlsx_file = self.mock_xlsx_file
        self.client.post(
            self.upload_url,
            {"file": xlsx_file},
            format="multipart",
        )

        self.assertTrue(mock_parse_set.called)
        self.assertTrue(mock_parse_label.called)
        self.assertTrue(mock_parse_annotation.called)
        self.assertTrue(mock_ingest.called)

        mock_ingest.assert_called_once_with(
            self.mock_annotation_set,
            self.mock_label_data,
            self.mock_annotation_data,
        )

    def test_upload_annotations_requires_file(self) -> None:
        """Test that uploading without a file is rejected by the serializer."""
        response = self.client.post(
            self.upload_url,
            {},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["file"][0], "No file was submitted.")

    @patch("api.views.annotation.parse_annotation_set_metadata")
    @patch("api.views.annotation.parse_label_set")
    @patch("api.views.annotation.parse_annotation_data")
    def test_upload_annotations_returns_400_if_parsing_fails(
        self, mock_parse_annotation: Mock, mock_parse_label: Mock, mock_parse_set: Mock
    ) -> None:
        """Test that uploading a file is rejected if parsing data fails with a ValueError."""
        mock_parse_set.side_effect = ValueError("Missing required metadata: Image Set Name")
        mock_parse_label.return_value = self.mock_label_data
        mock_parse_annotation.return_value = self.mock_annotation_data

        xlsx_file = self.mock_xlsx_file
        response = self.client.post(
            self.upload_url,
            {"file": xlsx_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Error parsing annotations template: Missing required metadata: Image Set Name", response.data["error"]
        )

    @patch("api.views.annotation.parse_annotation_set_metadata")
    @patch("api.views.annotation.parse_label_set")
    @patch("api.views.annotation.parse_annotation_data")
    @patch("api.views.annotation.ingest_annotation_data")
    def test_upload_annotations_returns_400_if_ingestion_fails(
        self, mock_ingest: Mock, mock_parse_annotation: Mock, mock_parse_label: Mock, mock_parse_set: Mock
    ) -> None:
        """Test that uploading a file is rejected if ingestion into DB fails with a ValueError."""
        mock_parse_set.side_effect = self.mock_annotation_set
        mock_parse_label.return_value = self.mock_label_data
        mock_parse_annotation.return_value = self.mock_annotation_data
        mock_ingest.side_effect = ValueError("Row 0: Image not found (UUID: , Name: fake_filename)")

        xlsx_file = self.mock_xlsx_file
        response = self.client.post(
            self.upload_url,
            {"file": xlsx_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Row 0: Image not found (UUID: , Name: fake_filename)", response.data["error"])
