"""Tests for AnnotationViewSet and UploadAnnotationsView."""

import io
import uuid
from unittest.mock import patch

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from api.models import Annotation
from api.models.annotation_set import AnnotationSet
from api.models.image_set import ImageSet
from api.tests.utils.auth_utils import AuthenticatedAPITestCase


class AnnotationViewSetTests(AuthenticatedAPITestCase):
    """Integration tests for AnnotationViewSet endpoints."""

    def setUp(self):
        """Set up test data and common variables."""
        super().setUp()
        self.annotation_set = AnnotationSet.objects.create(name="Test Set")
        self.image_set = ImageSet.objects.create(name="Test ImageSet")
        self.annotation_set.image_sets.set([self.image_set])
        self.image_a = self.image_set.images.create(filename="test_image.jpg", image_set=self.image_set)
        self.image_b = self.image_set.images.create(filename="test_image2.jpg", image_set=self.image_set)

        self.annotation_data = {
            "annotation_platform": "Test Platform",
            "shape": "rectangle",
            "coordinates": [[10, 10], [20, 20]],
        }

    def list_url(self):
        """Helper to get the list URL for AnnotationViewSet."""
        return reverse("annotation-list")

    def detail_url(self, pk):
        """Helper to get the detail URL for a specific Annotation."""
        return reverse("annotation-detail", kwargs={"pk": pk})

    def test_list_annotations(self):
        """Test listing Annotations."""
        annotation_data_b = {**self.annotation_data, "annotation_platform": "Another Platform"}
        Annotation.objects.create(annotation_set=self.annotation_set, image=self.image_a, **self.annotation_data)
        Annotation.objects.create(annotation_set=self.annotation_set, image=self.image_b, **annotation_data_b)
        self.client.force_authenticate(user=None)  # ensure endpoint works for anonymous users

        resp = self.client.get(self.list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(set(data.keys()), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 2)
        names = sorted([item["annotation_platform"] for item in data["results"]])
        self.assertEqual(names, ["Another Platform", "Test Platform"])

    def test_retrieve_annotation(self):
        """Test retrieving a specific Annotation."""
        annotation = Annotation.objects.create(
            annotation_set=self.annotation_set, image=self.image_a, **self.annotation_data
        )
        self.client.force_authenticate(user=None)  # ensure endpoint works for anonymous users

        resp = self.client.get(self.detail_url(annotation.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], str(annotation.pk))
        self.assertEqual(resp.data["annotation_platform"], "Test Platform")
        self.assertEqual(annotation.__str__(), f"Annotation({annotation.pk})")

    def test_create_annotation_with_image_that_does_not_exist(self):
        """Test that creating an Annotation with an image that does not exist is rejected."""
        payload = {
            **self.annotation_data,
            "image_id": uuid.uuid4(),
            "annotation_set_id": str(self.annotation_set.pk),
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_id", resp.data)

    def test_patch_annotation(self):
        """Test that PATCHing an Annotation."""
        annotation = Annotation.objects.create(
            image=self.image_a, annotation_set=self.annotation_set, **self.annotation_data
        )
        payload = {
            "annotation_platform": "Updated Platform",
        }

        resp = self.client.patch(self.detail_url(annotation.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        annotation.refresh_from_db()
        self.assertEqual(annotation.annotation_platform, "Updated Platform")

    def test_delete_annotation(self):
        """Test deleting an Annotation."""
        annotation = Annotation.objects.create(
            annotation_set=self.annotation_set, image=self.image_a, **self.annotation_data
        )

        resp = self.client.delete(self.detail_url(annotation.pk))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Annotation.objects.filter(pk=annotation.pk).exists())

    def test_anonymous_user_cannot_patch_annotation(self):
        """Test that an Annotation can't be PATCHed by an anonymous user."""
        annotation = Annotation.objects.create(
            image=self.image_a, annotation_set=self.annotation_set, **self.annotation_data
        )
        payload = {
            "annotation_platform": "Updated Platform",
        }
        self.client.force_authenticate(user=None)

        resp = self.client.patch(self.detail_url(annotation.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        annotation.refresh_from_db()
        self.assertEqual(annotation.annotation_platform, "Test Platform")


class UploadAnnotationsViewTests(AuthenticatedAPITestCase):
    """Tests for UploadAnnotationsView endpoints."""

    def setUp(self):
        """Set up test data and common variables."""
        super().setUp()
        self.upload_url = reverse("upload_annotation-list")
        self.mock_annotation_set = {"name": "Test Annotation Set"}
        self.mock_label_data = [{"name": "Label1", "parent": "Parent1"}]
        self.mock_annotation_data = [{"annotation": "data"}]

    def create_mock_xlsx_file(self):
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

    def test_upload_annotations_returns_201_resp_for_valid_xlsx_file(self):
        """Test successful upload of a valid XLSX file."""
        with (
            patch("api.views.annotation.parse_annotation_set_metadata") as mock_parse_set,
            patch("api.views.annotation.parse_label_set") as mock_parse_label,
            patch("api.views.annotation.parse_annotation_data") as mock_parse_annotation,
            patch("api.views.annotation.ingest_annotation_data") as mock_ingest,
        ):
            mock_parse_set.return_value = self.mock_annotation_set
            mock_parse_label.return_value = self.mock_label_data
            mock_parse_annotation.return_value = self.mock_annotation_data
            mock_ingest.return_value = {"status": "success", "count": 10}

            xlsx_file = self.create_mock_xlsx_file()
            response = self.client.post(
                self.upload_url,
                {"file": xlsx_file},
                format="multipart",
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["status"], "uploaded")
            self.assertEqual(response.data["data"]["status"], "success")
            self.assertEqual(response.data["data"]["count"], 10)

    def test_upload_annotations_rejects_non_xlsx_file(self):
        """Test that uploading a non-.xlsx file is rejected."""
        text_file = SimpleUploadedFile("test_file.txt", b"This is not an Excel file", content_type="text/plain")

        response = self.client.post(self.upload_url, {"file": text_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Provided file is not a .xlsx file.")

    def test_upload_annotations_rejects_invalid_excel_file(self):
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

    def test_upload_annotations_handles_missing_sheets(self):
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

    def test_upload_annotations_calls_parse_functions_correctly(self):
        """Test that the correct parse functions are called with the correct data."""
        with (
            patch("api.views.annotation.parse_annotation_set_metadata") as mock_parse_set,
            patch("api.views.annotation.parse_label_set") as mock_parse_label,
            patch("api.views.annotation.parse_annotation_data") as mock_parse_annotation,
            patch("api.views.annotation.ingest_annotation_data") as mock_ingest,
        ):
            mock_parse_set.return_value = self.mock_annotation_set
            mock_parse_label.return_value = self.mock_label_data
            mock_parse_annotation.return_value = self.mock_annotation_data
            mock_ingest.return_value = {}

            xlsx_file = self.create_mock_xlsx_file()
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

    def test_upload_annotations_requires_file(self):
        """Test that uploading without a file is rejected by the serializer."""
        response = self.client.post(
            self.upload_url,
            {},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["file"][0], "No file was submitted.")

    def test_upload_annotations_returns_400_if_parsing_fails(self):
        """Test that uploading a file is rejected if parsing data fails with a ValueError."""
        with (
            patch("api.views.annotation.parse_annotation_set_metadata") as mock_parse_set,
            patch("api.views.annotation.parse_label_set") as mock_parse_label,
            patch("api.views.annotation.parse_annotation_data") as mock_parse_annotation,
        ):
            mock_parse_set.side_effect = ValueError("Missing required metadata: Image Set Name")
            mock_parse_label.return_value = self.mock_label_data
            mock_parse_annotation.return_value = self.mock_annotation_data

            xlsx_file = self.create_mock_xlsx_file()
            response = self.client.post(
                self.upload_url,
                {"file": xlsx_file},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(
                "Error parsing annotations template: Missing required metadata: Image Set Name", response.data["error"]
            )

    def test_upload_annotations_returns_400_if_ingestion_fails(self):
        """Test that uploading a file is rejected if ingestion into DB fails with a ValueError."""
        with (
            patch("api.views.annotation.parse_annotation_set_metadata") as mock_parse_set,
            patch("api.views.annotation.parse_label_set") as mock_parse_label,
            patch("api.views.annotation.parse_annotation_data") as mock_parse_annotation,
            patch("api.views.annotation.ingest_annotation_data") as mock_ingest,
        ):
            mock_parse_set.side_effect = self.mock_annotation_set
            mock_parse_label.return_value = self.mock_label_data
            mock_parse_annotation.return_value = self.mock_annotation_data
            mock_ingest.side_effect = ValueError("Row 0: Image not found (UUID: , Name: fake_filename)")

            xlsx_file = self.create_mock_xlsx_file()
            response = self.client.post(
                self.upload_url,
                {"file": xlsx_file},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("Row 0: Image not found (UUID: , Name: fake_filename)", response.data["error"])
