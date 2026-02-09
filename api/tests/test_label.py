"""Tests for LabelViewSet."""

import uuid

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

    def list_url(self):
        """Helper to get the list URL for LabelViewSet."""
        return reverse("label-list")

    def detail_url(self, pk):
        """Helper to get the detail URL for a specific Label."""
        return reverse("label-detail", kwargs={"pk": pk})

    def test_list_labels(self):
        """Test listing Labels."""
        Label.objects.create(name="Test Label", annotation_set=self.annotation_set)
        Label.objects.create(name="Another Label", annotation_set=self.annotation_set)

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
        label = Label.objects.create(annotation_set=self.annotation_set, name="Test Label")
        payload = {
            "name": "Updated Label",
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
