"""Tests for ImageViewSet."""

import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Creator, Image, ImageSet, Project


class ImageViewSetTests(APITestCase):
    """Integration tests for ImageViewSet endpoints."""

    def setUp(self):
        """Set up test data and common variables."""
        self.creators_payload = [
            {"name": "Ada Lovelace", "uri": "https://example.com/people/ada"},
            {"name": "Grace Hopper", "uri": "https://example.com/people/grace"},
        ]

        self.project_payload = {"name": "Project 1", "uri": "https://example.com/project1"}

        self.image_set = ImageSet.objects.create(name="Test ImageSet")

    def list_url(self):
        """Helper to get the list URL for ImageViewSet."""
        return reverse("image-list")

    def detail_url(self, pk):
        """Helper to get the detail URL for a specific Image."""
        return reverse("image-detail", kwargs={"pk": pk})

    def test_list_images(self):
        """Test listing Images."""
        Image.objects.create(filename="file_a.jpg", image_set=self.image_set)
        Image.objects.create(filename="file_b.jpg", image_set=self.image_set)

        resp = self.client.get(self.list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        filenames = sorted([item["filename"] for item in data])
        self.assertEqual(filenames, ["file_a.jpg", "file_b.jpg"])

    def test_retrieve_image(self):
        """Test retrieving a specific Image."""
        image = Image.objects.create(filename="file_a.jpg", image_set=self.image_set)

        resp = self.client.get(self.detail_url(image.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], str(image.pk))
        self.assertEqual(resp.data["filename"], "file_a.jpg")
        self.assertEqual(image.__str__(), "file_a.jpg")

    def test_create_image_with_nested_creators(self):
        """Test creating an Image with nested creators."""
        payload = {
            "filename": "created_file.jpg",
            "creators": self.creators_payload,
            "image_set_id": str(self.image_set.pk),
            "latitude": 10.0,
            "longitude": 20.0,
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        image_id = resp.data["id"]
        image = Image.objects.get(pk=image_id)

        self.assertEqual(image.filename, "created_file.jpg")
        self.assertEqual(image.creators.count(), 2)

        self.assertTrue(Creator.objects.filter(name="Ada Lovelace").exists())

        self.assertIsNotNone(image.geom)

    def test_create_image_rejects_geom(self):
        """Test that creating an Image with a geom field is rejected, since geom is computed server-side."""
        payload = {
            "filename": "bad_image.jpg",
            "geom": {"type": "Point", "coordinates": [0, 0]},
            "image_set_id": str(self.image_set.pk),
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("geom", resp.data)

    def test_create_image_rejects_object_and_id_together(self):
        """Test that providing both nested object and ID for project is rejected."""
        existing = Project.objects.create(name="Existing Project", uri="https://example.com/existing")

        payload = {
            "filename": "bad_image.jpg",
            "project": {"name": "New Project", "uri": "https://example.com/new"},
            "project_id": str(existing.pk),
            "image_set_id": str(self.image_set.pk),
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", resp.data)

    def test_create_image_rejects_object_and_id_together_list(self):
        """Test that providing both nested object and ID for creators is rejected."""
        existing = Creator.objects.create(name="Existing Creator", uri="https://example.com/existing")

        payload = {
            "filename": "bad_image.jpg",
            "creators": [{"name": "New Creator", "uri": "https://example.com/new"}],
            "creators_ids": [str(existing.pk)],
            "image_set_id": str(self.image_set.pk),
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("creators", resp.data)

    def test_create_image_with_existing_ids(self):
        """Test creating an Image with existing creator IDs."""
        c1 = Creator.objects.create(name="Existing Creator 1", uri="https://example.com/c1")
        p1 = Project.objects.create(name="Existing Project 1", uri="https://example.com/p1")

        payload = {
            "filename": "created_file_via_ids.jpg",
            "creators_ids": [str(c1.pk)],
            "project_id": str(p1.pk),
            "image_set_id": str(self.image_set.pk),
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        image = Image.objects.get(pk=resp.data["id"])
        self.assertEqual(image.creators.count(), 1)
        self.assertEqual(image.creators.first().pk, c1.pk)
        self.assertEqual(image.project.pk, p1.pk)

    def test_create_image_with_same_filename(self):
        """Test that creating an Image with the same filename in the same ImageSet is rejected."""
        Image.objects.create(filename="file.jpg", image_set=self.image_set)

        payload = {
            "filename": "file.jpg",
            "image_set_id": str(self.image_set.pk),
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", resp.data)

    def test_create_image_with_image_set_that_does_not_exist(self):
        """Test that creating an Image with an image_set_id that does not exist is rejected."""
        payload = {
            "filename": "file.jpg",
            "image_set_id": uuid.uuid4(),
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_set_id", resp.data)

    def test_patch_image_replaces_one2m_with_nested_objects(self):
        """Test that PATCHing an Image with nested creators replaces the M2M relationships."""
        image = Image.objects.create(filename="original_file.jpg", image_set=self.image_set)
        old_project = Project.objects.create(name="Old Project", uri="https://example.com/old")
        image.project = old_project

        payload = {
            "filename": "updated_file.jpg",
            "project": {"name": "New Project", "uri": "https://example.com/new"},
            "image_set_id": str(self.image_set.pk),
        }

        resp = self.client.patch(self.detail_url(image.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        image.refresh_from_db()
        self.assertEqual(image.filename, "updated_file.jpg")
        self.assertEqual(image.project.name, "New Project")
        self.assertEqual(image.project.uri, "https://example.com/new")

    def test_patch_image_replaces_m2m_with_nested_objects(self):
        """Test that PATCHing an Image with nested creators and related materials replaces the M2M relationships."""
        image = Image.objects.create(filename="original_file.jpg", image_set=self.image_set)
        old_creator = Creator.objects.create(name="Old Creator", uri="https://example.com/old")
        image.creators.add(old_creator)

        payload = {
            "filename": "updated_file.jpg",
            "creators": [{"name": "New Creator", "uri": "https://example.com/new"}],
            "image_set_id": str(self.image_set.pk),
        }

        resp = self.client.patch(self.detail_url(image.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        image.refresh_from_db()
        self.assertEqual(image.filename, "updated_file.jpg")
        self.assertEqual(image.creators.count(), 1)
        self.assertEqual(image.creators.first().name, "New Creator")

    def test_delete_image(self):
        """Test deleting an Image."""
        image = Image.objects.create(filename="to_delete.jpg", image_set=self.image_set)

        resp = self.client.delete(self.detail_url(image.pk))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Image.objects.filter(pk=image.pk).exists())
