"""Tests for DebugDatabaseDumpView."""

from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.factories.annotation import AnnotationFactory, AnnotatorFactory
from api.factories.annotation_set import AnnotationSetFactory
from api.factories.image import ImageFactory
from api.factories.image_set import ImageSetFactory
from api.factories.label import LabelFactory
from api.models import AnnotationLabel


class SeedAndDatabaseDumpViewTests(APITestCase):
    """Integration tests for the seed demo data and debug database dump endpoints."""

    def url(self) -> str:
        """Helper method to get the URL for the debug database dump endpoint."""
        return reverse("debug-db-dump")

    @override_settings(DEBUG=True)
    def test_debug_dump_returns_payload_when_debug_true(self):
        """Test that the debug database dump endpoint returns data when DEBUG is True."""
        image_set = ImageSetFactory(
            with_relations=True, with_limits=True, creators=1, related_materials=1, with_camera_models=True
        )
        annotation_set = AnnotationSetFactory(with_relations=True, image_set_ids=[image_set.id])

        image = ImageFactory(image_set_id=image_set.id, with_relations=False, filename="test_image.jpg")

        label = LabelFactory(annotation_set_id=annotation_set.id, name="Test Label")
        annotator = AnnotatorFactory(name="Test Annotator")

        annotation = AnnotationFactory(
            image=image,
            annotation_set=annotation_set,
            shape="whole-image",
            coordinates=[[]],
        )

        AnnotationLabel.objects.create(
            annotation=annotation,
            label=label,
            annotator=annotator,
            creation_datetime="2025-01-01T00:00:00Z",
        )

        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertIsInstance(data, dict)

        for key in [
            "image_sets",
            "images",
            "annotation_sets",
            "labels",
            "annotators",
            "annotations",
            "annotation_labels",
        ]:
            self.assertIn(key, data)

        image_set_names = [row.get("name") for row in data["image_sets"]]
        self.assertIn(image_set.name, image_set_names)

        image_filenames = [row.get("filename") for row in data["images"]]
        self.assertIn(image.filename, image_filenames)

        annotation_set_names = [row.get("name") for row in data["annotation_sets"]]
        self.assertIn(annotation_set.name, annotation_set_names)

        label_names = [row.get("name") for row in data["labels"]]
        self.assertIn(label.name, label_names)

        annotator_names = [row.get("name") for row in data["annotators"]]
        self.assertIn(annotator.name, annotator_names)

        self.assertGreaterEqual(len(data["annotation_labels"]), 1)

    @override_settings(DEBUG=False)
    def test_debug_dump_returns_404_when_debug_false(self):
        """Test that the debug database dump endpoint returns 404 when DEBUG is False."""
        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {"detail": "Not found."})

    @override_settings(DEBUG=True)
    @patch("api.views.debug.tables_to_models_and_serializers", new={})
    def test_debug_dump_with_no_tables_returns_empty_payload(self):
        """Test that the debug database dump endpoint returns an empty payload if no tables are configured."""
        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {})
