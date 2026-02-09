"""Tests for AnnotationSetViewSet."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import AnnotationSet, Creator, Project
from api.models.image_set import ImageSet


class AnnotationSetViewSetTests(APITestCase):
    """Integration tests for AnnotationSetViewSet endpoints."""

    def setUp(self):
        """Set up test data and common variables."""
        self.creators_payload = [
            {"name": "Ada Lovelace", "uri": "https://example.com/people/ada"},
            {"name": "Grace Hopper", "uri": "https://example.com/people/grace"},
        ]

        self.project_payload = {"name": "Project 1", "uri": "https://example.com/project1"}

        self.image_set = ImageSet.objects.create(name="Test ImageSet")

    def list_url(self):
        """Helper to get the list URL for AnnotationSetViewSet."""
        return reverse("annotation_set-list")

    def detail_url(self, pk):
        """Helper to get the detail URL for a specific AnnotationSet."""
        return reverse("annotation_set-detail", kwargs={"pk": pk})

    def test_list_annotation_sets(self):
        """Test listing AnnotationSets."""
        annotation_set_a = AnnotationSet.objects.create(name="Set A")
        annotation_set_a.image_sets.set([self.image_set])
        annotation_set_b = AnnotationSet.objects.create(name="Set B")
        annotation_set_b.image_sets.set([self.image_set])

        resp = self.client.get(self.list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        names = sorted([item["name"] for item in data])
        self.assertEqual(names, ["Set A", "Set B"])

    def test_retrieve_annotation_set(self):
        """Test retrieving a specific AnnotationSet."""
        annotation_set = AnnotationSet.objects.create(name="Set A")
        annotation_set.image_sets.set([self.image_set])

        self.assertEqual(
            annotation_set.__str__(), f"AnnotationSet(id={annotation_set.pk}, version={annotation_set.version})"
        )

        resp = self.client.get(self.detail_url(annotation_set.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], str(annotation_set.pk))
        self.assertEqual(resp.data["name"], "Set A")

    def test_create_annotation_set_with_nested_creators(self):
        """Test creating an AnnotationSet with nested creators."""
        payload = {
            "name": "Created Set",
            "creators": self.creators_payload,
            "image_set_ids": [str(self.image_set.pk)],
        }

        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        annotation_set_id = resp.data["id"]
        annotation_set = AnnotationSet.objects.get(pk=annotation_set_id)

        self.assertEqual(annotation_set.name, "Created Set")
        self.assertEqual(annotation_set.creators.count(), 2)

        self.assertTrue(Creator.objects.filter(name="Ada Lovelace").exists())

        self.assertEqual(annotation_set.image_sets.count(), 1)

    def test_create_annotation_set_rejects_object_and_id_together(self):
        """Test that providing both nested object and ID for project is rejected."""
        existing = Project.objects.create(name="Existing Project", uri="https://example.com/existing")

        payload = {
            "name": "Bad Set",
            "project": {"name": "New Project", "uri": "https://example.com/new"},
            "project_id": str(existing.pk),
            "image_set_ids": [str(self.image_set.pk)],
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", resp.data)

    def test_create_annotation_set_rejects_object_and_id_together_list(self):
        """Test that providing both nested object and ID for creators is rejected."""
        existing = Creator.objects.create(name="Existing Creator", uri="https://example.com/existing")

        payload = {
            "name": "Bad Set",
            "creators": [{"name": "New Creator", "uri": "https://example.com/new"}],
            "creators_ids": [str(existing.pk)],
            "image_set_ids": [str(self.image_set.pk)],
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("creators", resp.data)

    def test_create_annotation_set_with_existing_ids(self):
        """Test creating an AnnotationSet with existing creator IDs."""
        c1 = Creator.objects.create(name="Existing Creator 1", uri="https://example.com/c1")
        p1 = Project.objects.create(name="Existing Project 1", uri="https://example.com/p1")

        payload = {
            "name": "Created Set via IDs",
            "creators_ids": [str(c1.pk)],
            "project_id": str(p1.pk),
            "image_set_ids": [str(self.image_set.pk)],
        }
        resp = self.client.post(self.list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        annotation_set = AnnotationSet.objects.get(pk=resp.data["id"])
        self.assertEqual(annotation_set.creators.count(), 1)
        self.assertEqual(annotation_set.creators.first().pk, c1.pk)
        self.assertEqual(annotation_set.project.pk, p1.pk)

    def test_patch_annotation_set_replaces_one2m_with_nested_objects(self):
        """Test that PATCHing an AnnotationSet with nested creators replaces the M2M relationships."""
        annotation_set = AnnotationSet.objects.create(name="Original")
        annotation_set.image_sets.set([self.image_set])
        old_project = Project.objects.create(name="Old Project", uri="https://example.com/old")
        annotation_set.project = old_project

        payload = {
            "name": "Updated",
            "project": {"name": "New Project", "uri": "https://example.com/new"},
        }

        resp = self.client.patch(self.detail_url(annotation_set.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        annotation_set.refresh_from_db()
        self.assertEqual(annotation_set.name, "Updated")
        self.assertEqual(annotation_set.project.name, "New Project")
        self.assertEqual(annotation_set.project.uri, "https://example.com/new")

    def test_patch_annotation_set_replaces_m2m_with_nested_objects(self):
        """Test that PATCHing an AnnotationSet with nested creators replaces the M2M relationships."""
        annotation_set = AnnotationSet.objects.create(name="Original")
        annotation_set.image_sets.set([self.image_set])
        old_creator = Creator.objects.create(name="Old Creator", uri="https://example.com/old")
        annotation_set.creators.add(old_creator)

        payload = {
            "name": "Updated",
            "creators": [{"name": "New Creator", "uri": "https://example.com/new"}],
        }

        resp = self.client.patch(self.detail_url(annotation_set.pk), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        annotation_set.refresh_from_db()
        self.assertEqual(annotation_set.name, "Updated")
        self.assertEqual(annotation_set.creators.count(), 1)
        self.assertEqual(annotation_set.creators.first().name, "New Creator")

    def test_delete_annotation_set(self):
        """Test deleting an AnnotationSet."""
        annotation_set = AnnotationSet.objects.create(name="To Delete")
        annotation_set.image_sets.set([self.image_set])

        resp = self.client.delete(self.detail_url(annotation_set.pk))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AnnotationSet.objects.filter(pk=annotation_set.pk).exists())
