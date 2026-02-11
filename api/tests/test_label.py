"""Tests for LabelViewSet."""

import uuid
from unittest.mock import Mock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Label
from api.models.annotation_set import AnnotationSet
from api.models.image_set import ImageSet


class LabelViewSetTests(APITestCase):
    """Integration tests for LabelViewSet endpoints."""

    def setUp(self):
        """Set up test data and common variables."""
        self.annotation_set = AnnotationSet.objects.create(name="Test Set")
        self.image_set = ImageSet.objects.create(name="Test ImageSet")
        self.annotation_set.image_sets.set([self.image_set])

        self._worms_patcher = patch("api.serializers.label._test_cached_and_live_worms_api")
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
        self.mocked_worms.return_value = Mock(status_code=404)

        payload = {
            "name": "Label With Aphia",
            "annotation_set_id": self.annotation_set.pk,
            "lowest_aphia_id": "999999999",
            "parent_label_name": "Parent Label",
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lowest_aphia_id", resp.data)

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
        """Test that creating a Label with an empty lowest_aphia_id is accepted."""
        payload = {
            "name": "Valid Aphia Label",
            "annotation_set_id": self.annotation_set.pk,
            "parent_label_name": "Parent Label",
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

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
