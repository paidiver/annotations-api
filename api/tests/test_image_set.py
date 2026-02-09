"""Tests for ImageSetViewSet."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Creator, ImageSet, Project, RelatedMaterial


class ImageSetViewSetTests(APITestCase):
    """Integration tests for ImageSetViewSet endpoints."""

    def setUp(self):
        """Set up test data and common variables."""
        self.creators_payload = [
            {"name": "Ada Lovelace", "uri": "https://example.com/people/ada"},
            {"name": "Grace Hopper", "uri": "https://example.com/people/grace"},
        ]
        self.materials_payload = [
            {"uri": "https://example.com/paper.pdf", "title": "Paper", "relation": "Describes the dataset."},
            {"uri": "https://example.com/readme", "title": "README", "relation": "How to use the dataset."},
        ]

        self.project_payload = {"name": "Project 1", "uri": "https://example.com/project1"}

    def list_url(self):
        """Helper to get the list URL for ImageSetViewSet."""
        return reverse("image_set-list")

    def detail_url(self, pk):
        """Helper to get the detail URL for a specific ImageSet."""
        return reverse("image_set-detail", kwargs={"pk": pk})

    def test_list_image_sets(self):
        """Test listing ImageSets."""
        ImageSet.objects.create(name="Set A")
        ImageSet.objects.create(name="Set B")

        resp = self.client.get(self.list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        names = sorted([item["name"] for item in data])
        self.assertEqual(names, ["Set A", "Set B"])

    def test_retrieve_image_set(self):
        """Test retrieving a specific ImageSet."""
        image_set = ImageSet.objects.create(name="Set A")

        resp = self.client.get(self.detail_url(image_set.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], str(image_set.pk))
        self.assertEqual(resp.data["name"], "Set A")

    def test_create_image_set_with_nested_creators_and_materials(self):
        """Test creating an ImageSet with nested creators and related materials."""
        payload = {
            "name": "Created Set",
            "creators": self.creators_payload,
            "related_materials": self.materials_payload,
            "min_latitude_degrees": -10.0,
            "max_latitude_degrees": 10.0,
            "min_longitude_degrees": 20.0,
            "max_longitude_degrees": 30.0,
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        image_set_id = resp.data["id"]
        image_set = ImageSet.objects.get(pk=image_set_id)

        self.assertEqual(image_set.name, "Created Set")
        self.assertEqual(image_set.creators.count(), 2)
        self.assertEqual(image_set.related_materials.count(), 2)

        self.assertTrue(Creator.objects.filter(name="Ada Lovelace").exists())
        self.assertTrue(RelatedMaterial.objects.filter(uri="https://example.com/paper.pdf").exists())

        # limits is computed in ImageSet.save() when bbox is present
        self.assertIsNotNone(image_set.limits)

    def test_create_image_set_rejects_geom(self):
        """Test that creating an ImageSet with a geom field is rejected, since geom is computed server-side."""
        payload = {
            "name": "Bad Set",
            "geom": {"type": "Point", "coordinates": [0, 0]},
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("geom", resp.data)

    def test_create_image_set_rejects_object_and_id_together(self):
        """Test that providing both nested object and ID for project is rejected."""
        existing = Project.objects.create(name="Existing Project", uri="https://example.com/existing")

        payload = {
            "name": "Bad Set",
            "project": {"name": "New Project", "uri": "https://example.com/new"},
            "project_id": str(existing.pk),
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", resp.data)

    def test_create_image_set_rejects_object_and_id_together_list(self):
        """Test that providing both nested object and ID for creators is rejected."""
        existing = Creator.objects.create(name="Existing Creator", uri="https://example.com/existing")

        payload = {
            "name": "Bad Set",
            "creators": [{"name": "New Creator", "uri": "https://example.com/new"}],
            "creators_ids": [str(existing.pk)],
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("creators", resp.data)

    def test_create_image_set_with_existing_ids(self):
        """Test creating an ImageSet with existing creator and related material IDs."""
        c1 = Creator.objects.create(name="Existing Creator 1", uri="https://example.com/c1")
        m1 = RelatedMaterial.objects.create(uri="https://example.com/m1", title="M1")
        p1 = Project.objects.create(name="Existing Project 1", uri="https://example.com/p1")

        payload = {
            "name": "Created Set via IDs",
            "creators_ids": [str(c1.pk)],
            "related_materials_ids": [str(m1.pk)],
            "project_id": str(p1.pk),
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        image_set = ImageSet.objects.get(pk=resp.data["id"])
        self.assertEqual(image_set.creators.count(), 1)
        self.assertEqual(image_set.related_materials.count(), 1)
        self.assertEqual(image_set.creators.first().pk, c1.pk)
        self.assertEqual(image_set.related_materials.first().pk, m1.pk)
        self.assertEqual(image_set.project.pk, p1.pk)

    def test_patch_image_set_replaces_one2m_with_nested_objects(self):
        """Test that PATCHing an ImageSet with nested creators and related materials replaces the M2M relationships."""
        image_set = ImageSet.objects.create(name="Original")
        old_project = Project.objects.create(name="Old Project", uri="https://example.com/old")
        image_set.project = old_project

        payload = {
            "name": "Updated",
            "project": {"name": "New Project", "uri": "https://example.com/new"},
        }

        resp = self.client.patch(self.detail_url(image_set.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        image_set.refresh_from_db()
        self.assertEqual(image_set.name, "Updated")
        self.assertEqual(image_set.project.name, "New Project")
        self.assertEqual(image_set.project.uri, "https://example.com/new")

    def test_patch_image_set_replaces_m2m_with_nested_objects(self):
        """Test that PATCHing an ImageSet with nested creators and related materials replaces the M2M relationships."""
        image_set = ImageSet.objects.create(name="Original")
        old_creator = Creator.objects.create(name="Old Creator", uri="https://example.com/old")
        old_material = RelatedMaterial.objects.create(uri="https://example.com/old-m", title="Old")
        image_set.creators.add(old_creator)
        image_set.related_materials.add(old_material)

        payload = {
            "name": "Updated",
            "creators": [{"name": "New Creator", "uri": "https://example.com/new"}],
            "related_materials": [{"uri": "https://example.com/new-m", "title": "New"}],
        }

        resp = self.client.patch(self.detail_url(image_set.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        image_set.refresh_from_db()
        self.assertEqual(image_set.name, "Updated")
        self.assertEqual(image_set.creators.count(), 1)
        self.assertEqual(image_set.related_materials.count(), 1)
        self.assertEqual(image_set.creators.first().name, "New Creator")
        self.assertEqual(image_set.related_materials.first().uri, "https://example.com/new-m")

    def test_patch_image_set_rejects_min_max_lat_lon(self):
        """Test that PATCHing an ImageSet with invalid min/max latitude values is rejected."""
        image_set = ImageSet.objects.create(name="Original")

        payload = {
            "min_latitude_degrees": 10.0,
            "max_latitude_degrees": 5.0,
        }
        resp = self.client.patch(self.detail_url(image_set.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("min_latitude_degrees", resp.data)

    def test_delete_image_set(self):
        """Test deleting an ImageSet."""
        image_set = ImageSet.objects.create(name="To Delete")

        resp = self.client.delete(self.detail_url(image_set.pk))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ImageSet.objects.filter(pk=image_set.pk).exists())
