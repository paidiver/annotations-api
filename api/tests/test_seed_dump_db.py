"""Tests for DebugDatabaseDumpView."""

from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.factories.annotation import AnnotatorFactory
from api.factories.annotation_set import AnnotationSetFactory
from api.factories.image import ImageFactory
from api.factories.image_set import ImageSetFactory
from api.models import Annotation, AnnotationSetModel, Label, LabelSet


class SeedAndDatabaseDumpViewTests(APITestCase):
    """Integration tests for the seed demo data and debug database dump endpoints."""

    def url(self) -> str:
        """Helper method to get the URL for the debug database dump endpoint."""
        return reverse("debug-db-dump")

    @override_settings(DEBUG=True)
    def test_debug_dump_returns_payload_when_debug_true(self) -> None:
        """Test that the debug database dump endpoint returns data when DEBUG is True."""
        image_set = ImageSetFactory(
            with_relations=True, with_limits=True, creators=1, related_materials=1, with_camera_models=True
        )
        annotation_set = AnnotationSetFactory(with_relations=True, image_set_ids=[image_set.id])

        image = ImageFactory(image_set_id=image_set.id, with_relations=False, filename="test_image.jpg")

        label_set = LabelSet.objects.create(name="Test Label Set")
        annotation_set.label_sets.add(label_set)
        label = Label.objects.create(label_set=label_set, name="Test Label")
        annotator = AnnotatorFactory(name="Test Annotator")

        annotation_model = AnnotationSetModel.objects.create(
            annotation_set=annotation_set,
            model_id="test-model",
            name="Test Model",
            version="1.0",
            task="classification",
        )
        annotation = Annotation.objects.create(
            image=image,
            annotation_set=annotation_set,
            label=label,
            human_or_machine="human",
            shape="whole-image",
            coordinates=[[]],
        )
        annotation.creators.add(annotator)

        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertIsInstance(data, dict)

        for key in [
            "image_sets",
            "images",
            "annotation_sets",
            "annotation_set_models",
            "label_sets",
            "labels",
            "annotators",
            "annotations",
        ]:
            self.assertIn(key, data)

        image_set_names = [row.get("name") for row in data["image_sets"]]
        self.assertIn(image_set.name, image_set_names)

        image_filenames = [row.get("filename") for row in data["images"]]
        self.assertIn(image.filename, image_filenames)

        annotation_set_names = [row.get("name") for row in data["annotation_sets"]]
        self.assertIn(annotation_set.name, annotation_set_names)

        label_set_names = [row.get("name") for row in data["label_sets"]]
        self.assertIn(label_set.name, label_set_names)

        annotation_model_names = [row.get("name") for row in data["annotation_set_models"]]
        self.assertIn(annotation_model.name, annotation_model_names)

        label_names = [row.get("name") for row in data["labels"]]
        self.assertIn(label.name, label_names)

        annotator_names = [row.get("name") for row in data["annotators"]]
        self.assertIn(annotator.name, annotator_names)

        self.assertGreaterEqual(len(data["annotations"]), 1)

    @override_settings(DEBUG=False)
    def test_debug_dump_returns_404_when_debug_false(self) -> None:
        """Test that the debug database dump endpoint returns 404 when DEBUG is False."""
        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data["detail"], "Not found.")
        self.assertEqual(resp.data["code"], "not_found")

    @override_settings(DEBUG=True)
    @patch("api.views.debug.tables_to_models_and_serializers", new={})
    def test_debug_dump_with_no_tables_returns_empty_payload(self) -> None:
        """Test that the debug database dump endpoint returns an empty payload if no tables are configured."""
        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {})
