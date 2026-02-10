"""Tests for AnnotationLabelViewSet."""

import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import AnnotationLabel
from api.models.annotation import Annotation, Annotator
from api.models.annotation_set import AnnotationSet
from api.models.image import Image
from api.models.image_set import ImageSet
from api.models.label import Label


class AnnotationLabelViewSetTests(APITestCase):
    """Integration tests for AnnotationLabelViewSet endpoints."""

    def setUp(self):
        """Set up test data and common variables."""
        self.annotation_set = AnnotationSet.objects.create(name="Test Set")
        self.image_set = ImageSet.objects.create(name="Test ImageSet")
        self.annotation_set.image_sets.set([self.image_set])
        self.image = Image.objects.create(filename="test_image.jpg", image_set=self.image_set)
        self.annotation = Annotation.objects.create(
            annotation_set=self.annotation_set,
            image=self.image,
            shape="rectangle",
            coordinates=[[10, 10], [20, 20]],
        )
        self.label = Label.objects.create(name="A Label", annotation_set=self.annotation_set)

        self.annotator = Annotator.objects.create(name="Test Annotator")

    def list_url(self):
        """Helper to get the list URL for AnnotationLabelViewSet."""
        return reverse("annotation_label-list")

    def detail_url(self, pk):
        """Helper to get the detail URL for a specific AnnotationLabel."""
        return reverse("annotation_label-detail", kwargs={"pk": pk})

    def test_list_annotation_labels(self):
        """Test listing AnnotationLabels."""
        label1 = Label.objects.create(name="Test Label", annotation_set=self.annotation_set)
        label2 = Label.objects.create(name="Another Label", annotation_set=self.annotation_set)

        AnnotationLabel.objects.create(
            annotation=self.annotation, label=label1, annotator=self.annotator, creation_datetime="2024-01-01T00:00:00Z"
        )
        AnnotationLabel.objects.create(
            annotation=self.annotation, label=label2, annotator=self.annotator, creation_datetime="2024-01-02T00:00:00Z"
        )

        resp = self.client.get(self.list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        creation_datetimes = sorted([item["creation_datetime"] for item in data])
        self.assertEqual(creation_datetimes, ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"])

    def test_retrieve_annotation_label(self):
        """Test retrieving a specific AnnotationLabel."""
        annotation_label = AnnotationLabel.objects.create(
            creation_datetime="2024-01-01T00:00:00Z",
            annotation=self.annotation,
            label=self.label,
            annotator=self.annotator,
        )

        resp = self.client.get(self.detail_url(annotation_label.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], str(annotation_label.pk))
        self.assertEqual(resp.data["creation_datetime"], "2024-01-01T00:00:00Z")
        self.assertEqual(
            annotation_label.__str__(), f"AnnotationLabel(annotation={self.annotation.pk}, label={self.label.pk})"
        )
        self.assertEqual(self.annotator.__str__(), self.annotator.name)

    def test_create_annotation_label_with_annotator_set_that_does_not_exist(self):
        """Test that creating an AnnotationLabel with an annotator set that does not exist is rejected."""
        payload = {
            "creation_datetime": "2024-01-01T00:00:00Z",
            "annotation_id": str(self.annotation.pk),
            "label_id": str(self.label.pk),
            "annotator_id": uuid.uuid4(),
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("annotator_id", resp.data)

    def test_create_annotation_label_with_same_foreign_key(self):
        """Test that creating an AnnotationLabel with same foreign key is rejected."""
        AnnotationLabel.objects.create(
            creation_datetime="2024-01-01T00:00:00Z",
            annotation=self.annotation,
            label=self.label,
            annotator=self.annotator,
        )
        payload = {
            "creation_datetime": "2024-01-01T00:00:00Z",
            "annotation_id": str(self.annotation.pk),
            "label_id": str(self.label.pk),
            "annotator_id": str(self.annotator.pk),
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", resp.data)

    def test_patch_annotation_label(self):
        """Test that PATCHing an AnnotationLabel."""
        annotation_label = AnnotationLabel.objects.create(
            creation_datetime="2024-01-01T00:00:00Z",
            annotation=self.annotation,
            label=self.label,
            annotator=self.annotator,
        )
        payload = {
            "creation_datetime": "2024-01-02T00:00:00Z",
        }

        resp = self.client.patch(self.detail_url(annotation_label.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["creation_datetime"], "2024-01-02T00:00:00Z")

    def test_delete_annotation_label(self):
        """Test deleting an AnnotationLabel."""
        annotation_label = AnnotationLabel.objects.create(
            creation_datetime="2024-01-01T00:00:00Z",
            annotation=self.annotation,
            label=self.label,
            annotator=self.annotator,
        )

        resp = self.client.delete(self.detail_url(annotation_label.pk))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AnnotationLabel.objects.filter(pk=annotation_label.pk).exists())
