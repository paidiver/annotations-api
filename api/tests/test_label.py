"""Tests for LabelViewSet."""

import uuid
from unittest.mock import Mock, patch

from django.urls import reverse
from requests.exceptions import Timeout
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Label
from api.models.annotation_set import AnnotationSet
from api.models.image_set import ImageSet
from api.serializers.label import LabelSerializer


class LabelViewSetTests(APITestCase):
    """Integration tests for LabelViewSet endpoints."""

    def setUp(self):
        """Set up test data and common variables."""
        self.annotation_set = AnnotationSet.objects.create(name="Test Set")
        self.image_set = ImageSet.objects.create(name="Test ImageSet")
        self.annotation_set.image_sets.set([self.image_set])

        self._worms_patcher = patch("api.serializers.label._ingest_get_aphia_id_cached_worms")
        self.mocked_worms = self._worms_patcher.start()
        self.addCleanup(self._worms_patcher.stop)

        self.mocked_worms.return_value = Mock(status_code=200)

    def list_url(self):
        """Helper to get the list URL for LabelViewSet."""
        return reverse("label-list")

    def detail_url(self, pk):
        """Helper to get the detail URL for a specific Label."""
        return reverse("label-detail", kwargs={"pk": pk})

    def test_create_label_rejects_invalid_lowest_aphia_id(self):
        """Test that creating a Label with an invalid lowest_aphia_id is rejected."""
        payload = {
            "name": "Label With Aphia",
            "annotation_set_id": self.annotation_set.pk,
            "lowest_aphia_id": "999999999",
            "parent_label_name": "Parent Label",
        }
        self.mocked_worms.return_value = Mock(status_code=400)
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lowest_aphia_id", resp.data)
        self.assertIn(
            resp.data["lowest_aphia_id"][0],
            [
                "WoRMS API is currently unavailable. Please try again later.",
                "Invalid lowest_aphia_id: 999999999 does not exist in WoRMS API.",
            ],
        )

        self.mocked_worms.return_value = Mock(status_code=500)
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lowest_aphia_id", resp.data)
        self.assertIn(
            resp.data["lowest_aphia_id"][0],
            ["Unable to validate lowest_aphia_id right now (status 500). Please try again later."],
        )

    def test_create_label_rejects_timeout(self):
        """Test that creating a Label when the WoRMS API times out is rejected."""
        self.mocked_worms.side_effect = Timeout()
        payload = {
            "name": "Label With Aphia",
            "annotation_set_id": self.annotation_set.pk,
            "lowest_aphia_id": "12345",
            "parent_label_name": "Parent Label",
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lowest_aphia_id", resp.data)
        self.assertIn(resp.data["lowest_aphia_id"][0], ["WoRMS API is currently unavailable. Please try again later."])

    def test_create_label_rejects_different_error(self):
        """Test that creating a Label when the WoRMS API returns a different error is rejected."""
        self.mocked_worms.return_value = Mock(status_code=418)
        payload = {
            "name": "Label With Aphia",
            "annotation_set_id": self.annotation_set.pk,
            "lowest_aphia_id": "12345",
            "parent_label_name": "Parent Label",
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lowest_aphia_id", resp.data)

        expected_msg = (
            f"Unable to validate lowest_aphia_id right now (status {self.mocked_worms.return_value.status_code}). "
            "Please try again later."
        )
        self.assertEqual(str(resp.data["lowest_aphia_id"][0]), expected_msg)

    def test_create_label_accepts_valid_lowest_aphia_id(self):
        """Test that creating a Label with a valid lowest_aphia_id is accepted."""
        self.mocked_worms.return_value = Mock(status_code=200)

        payload = {
            "name": "Valid Aphia Label",
            "annotation_set_id": self.annotation_set.pk,
            "lowest_aphia_id": "12345",
            "parent_label_name": "Parent Label",
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_label_with_empty_aphia_id(self):
        """Test that creating a Label with an empty lowest_aphia_id is rejected."""
        payload = {
            "name": "Valid Aphia Label",
            "annotation_set_id": self.annotation_set.pk,
            "parent_label_name": "Parent Label",
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_labels(self):
        """Test listing Labels."""
        Label.objects.create(name="Test Label", annotation_set=self.annotation_set, parent_label_name="Parent Label")
        Label.objects.create(name="Another Label", annotation_set=self.annotation_set, parent_label_name="Parent Label")

        resp = self.client.get(self.list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        names = sorted([item["name"] for item in data])
        self.assertEqual(names, ["Another Label", "Test Label"])

    def test_retrieve_label(self):
        """Test retrieving a specific Label."""
        label = Label.objects.create(annotation_set=self.annotation_set, name="Test Label")
        resp = self.client.get(self.detail_url(label.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], str(label.pk))
        self.assertEqual(resp.data["name"], "Test Label")
        self.assertEqual(label.__str__(), "Test Label")

    def test_create_label_with_annotation_set_that_does_not_exist(self):
        """Test that creating an Label with an annotation set that does not exist is rejected."""
        payload = {
            "name": "Test Label",
            "parent_label_name": "Parent Label",
            "annotation_set_id": uuid.uuid4(),
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("annotation_set_id", resp.data)

    def test_patch_label(self):
        """Test that PATCHing an Label."""
        self.mocked_worms.return_value = Mock(status_code=200)

        label = Label.objects.create(annotation_set=self.annotation_set, name="Test Label")
        payload = {
            "name": "Updated Label",
            "lowest_aphia_id": "12345",
        }

        resp = self.client.patch(self.detail_url(label.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        label.refresh_from_db()
        self.assertEqual(label.name, "Updated Label")

    def test_delete_label(self):
        """Test deleting an Label."""
        label = Label.objects.create(annotation_set=self.annotation_set, name="Test Label")

        resp = self.client.delete(self.detail_url(label.pk))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Label.objects.filter(pk=label.pk).exists())

    def test_validate_aphia_id_uses_context_cache(self):
        """Test that the same aphia_id is only validated once per shared serializer context."""
        self.mocked_worms.return_value = Mock(status_code=200)

        shared_context = {"aphia_validation_error_cache": {}}

        payload_1 = {
            "name": "Label One",
            "annotation_set_id": self.annotation_set.pk,
            "lowest_aphia_id": "12345",
            "parent_label_name": "Parent Label",
        }
        payload_2 = {
            "name": "Label Two",
            "annotation_set_id": self.annotation_set.pk,
            "lowest_aphia_id": "12345",
            "parent_label_name": "Parent Label",
        }

        serializer_1 = LabelSerializer(data=payload_1, context=shared_context)
        serializer_2 = LabelSerializer(data=payload_2, context=shared_context)

        self.assertTrue(serializer_1.is_valid(), serializer_1.errors)
        self.assertTrue(serializer_2.is_valid(), serializer_2.errors)

        self.mocked_worms.assert_called_once_with("12345")
        self.assertIn("12345", shared_context["aphia_validation_error_cache"])
        self.assertIsNone(shared_context["aphia_validation_error_cache"]["12345"])

    def test_validate_aphia_id_caches_invalid_result(self):
        """Test that an invalid aphia_id result is cached and not requested twice."""
        self.mocked_worms.return_value = Mock(status_code=400)

        shared_context = {"aphia_validation_error_cache": {}}

        payload = {
            "name": "Invalid Aphia Label",
            "annotation_set_id": self.annotation_set.pk,
            "lowest_aphia_id": "999999999",
            "parent_label_name": "Parent Label",
        }

        serializer_1 = LabelSerializer(data=payload, context=shared_context)
        serializer_2 = LabelSerializer(data=payload, context=shared_context)

        self.assertFalse(serializer_1.is_valid())
        self.assertFalse(serializer_2.is_valid())

        self.mocked_worms.assert_called_once_with("999999999")
        self.assertEqual(
            shared_context["aphia_validation_error_cache"]["999999999"],
            "Invalid lowest_aphia_id: 999999999 does not exist in WoRMS API.",
        )
