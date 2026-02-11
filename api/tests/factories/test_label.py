"""Tests for the LabelFactory, ensuring that it correctly handles related fields and annotation sets."""

from django.test import TestCase

from api.factories.annotation_set import AnnotationSetFactory
from api.factories.label import LabelFactory


class LabelFactoryCoverageTests(TestCase):
    """Tests for the LabelFactory, ensuring that it correctly handles related fields and annotation sets."""

    def test_label_with_both_annotation_set_id_object_reject(self):
        """Creating a Label with both annotation_set and annotation_set_id raises a ValueError."""
        with self.assertRaises(ValueError):
            LabelFactory(annotation_set=AnnotationSetFactory(), annotation_set_id=1)
