"""Tests for ingest_ifdo_image_set view."""

from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from api.ingest.data_subs_mapping import IFDOAdaptError
from api.models import Image, ImageSet


class IngestIFDOViewTests(APITestCase):
    """Integration tests for ingest_ifdo_image_set endpoint."""

    def ingest_url(self):
        """Helper to get the ingest URL."""
        return "/api/ingest/image-set"

    @patch("api.views.ingest_imagery.adapt_ifdo_item_to_image_serializer_payload")
    @patch("api.views.ingest_imagery.adapt_ifdo_image_set_to_serializer_payload")
    def test_ingest_ifdo_success_creates_imageset_and_images(self, mock_adapt_set: Mock, mock_adapt_item: Mock):
        """POST should create ImageSet and Images and return 201.

        Args:
            mock_adapt_set: Mock for the ImageSet adapter function.
            mock_adapt_item: Mock for the Image adapter function.
        """
        image_set = ImageSet.objects.create(name="Existing Set")
        mock_adapt_set.return_value = {"name": "My IFDO ImageSet"}
        mock_adapt_item.side_effect = [
            {"filename": "a.jpg", "image_set_id": image_set.id},
            {"filename": "b.jpg", "image_set_id": image_set.id},
        ]

        payload = {
            "submission_id": "sub-123",
            "ifdo": {
                "image-set-header": {"image-set-name": "ok"},
                "image-set-items": [{"x": 1}, {"x": 2}],
            },
        }

        resp = self.client.post(self.ingest_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["message"], "Ingested iFDO payload successfully")
        self.assertEqual(resp.data["image_count"], 2)

        image_set = ImageSet.objects.get(pk=resp.data["image_set_id"])
        self.assertEqual(image_set.name, "My IFDO ImageSet")

        filenames = sorted(Image.objects.filter(image_set=image_set).values_list("filename", flat=True))
        self.assertEqual(filenames, ["a.jpg", "b.jpg"])

        mock_adapt_set.assert_called_once()
        self.assertEqual(mock_adapt_item.call_count, 2)

    def test_ingest_ifdo_missing_ifdo_returns_400(self):
        """POST without ifdo object should return 400."""
        resp = self.client.post(self.ingest_url(), {"submission_id": "sub-123"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["detail"], "Missing or invalid 'ifdo' object")

    def test_ingest_ifdo_ifdo_not_dict_returns_400(self):
        """POST with non-dict ifdo should return 400."""
        resp = self.client.post(self.ingest_url(), {"ifdo": "nope"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["detail"], "Missing or invalid 'ifdo' object")

    @patch("api.views.ingest_imagery.adapt_ifdo_image_set_to_serializer_payload")
    def test_ingest_ifdo_adapter_error_on_imageset_returns_400(self, mock_adapt_set: Mock):
        """If ImageSet adapter raises IFDOAdaptError, return 400.

        Args:
            mock_adapt_set: Mock for the ImageSet adapter function.
        """
        mock_adapt_set.side_effect = IFDOAdaptError("bad header")

        resp = self.client.post(self.ingest_url(), {"ifdo": {"image-set-items": []}}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["detail"], "bad header")

    def test_ingest_ifdo_items_not_list_returns_400(self):
        """ifdo.image-set-items must be a list."""
        resp = self.client.post(
            self.ingest_url(),
            {"ifdo": {"image-set-header": {"image-set-name": "ok"}, "image-set-items": {"not": "a list"}}},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["detail"], "ifdo.image-set-items must be a list")

    @patch("api.views.ingest_imagery.adapt_ifdo_image_set_to_serializer_payload")
    def test_ingest_ifdo_imageset_serializer_invalid_returns_400(self, mock_adapt_set: Mock):
        """If ImageSetSerializer fails validation, return 400 with image_set errors.

        Args:
            mock_adapt_set: Mock for the ImageSet adapter function.
        """
        mock_adapt_set.return_value = {"name": ""}

        resp = self.client.post(
            self.ingest_url(),
            {"ifdo": {"image-set-items": []}},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_set", resp.data)

        self.assertEqual(ImageSet.objects.count(), 0)

    @patch("api.views.ingest_imagery.adapt_ifdo_item_to_image_serializer_payload")
    @patch("api.views.ingest_imagery.adapt_ifdo_image_set_to_serializer_payload")
    def test_ingest_ifdo_item_errors_roll_back_everything(self, mock_adapt_set: Mock, mock_adapt_item: Mock):
        """If any item fails, view should return 400 and rollback ImageSet + Images.

        Args:
            mock_adapt_set: Mock for the ImageSet adapter function.
            mock_adapt_item: Mock for the Image adapter function.
        """
        mock_adapt_set.return_value = {"name": "Will Rollback"}
        mock_adapt_item.side_effect = [
            {"filename": "a.jpg", "image_set_id": 999},
            IFDOAdaptError("bad item"),
        ]

        payload = {
            "ifdo": {
                "image-set-items": [{"ok": True}, {"ok": False}],
            }
        }

        resp = self.client.post(self.ingest_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["detail"], "One or more image items failed validation")
        self.assertIn("items", resp.data)
        self.assertIn("2", resp.data["items"])
        self.assertEqual(resp.data["items"]["2"]["detail"], "bad item")

        self.assertEqual(ImageSet.objects.count(), 0)
        self.assertEqual(Image.objects.count(), 0)

    @patch("api.views.ingest_imagery.adapt_ifdo_item_to_image_serializer_payload")
    @patch("api.views.ingest_imagery.adapt_ifdo_image_set_to_serializer_payload")
    def test_ingest_ifdo_non_dict_item_is_reported_and_rolls_back(self, mock_adapt_set: Mock, mock_adapt_item: Mock):
        """Non-dict items should be reported and cause rollback.

        Args:
            mock_adapt_set: Mock for the ImageSet adapter function.
            mock_adapt_item: Mock for the Image adapter function.
        """
        mock_adapt_set.return_value = {"name": "Rollback Non-Dict Item"}
        mock_adapt_item.return_value = {"filename": "a.jpg", "image_set_id": 999}

        payload = {
            "ifdo": {
                "image-set-items": [{"ok": True}, "not-an-object"],
            }
        }

        resp = self.client.post(self.ingest_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", resp.data)
        self.assertIn("2", resp.data["items"])
        self.assertEqual(resp.data["items"]["2"]["detail"], "Item must be an object")

        self.assertEqual(ImageSet.objects.count(), 0)
        self.assertEqual(Image.objects.count(), 0)
