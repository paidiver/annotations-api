"""Tests for AnnotationViewSet."""

import uuid

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
        names = sorted([item["annotation_platform"] for item in data])
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