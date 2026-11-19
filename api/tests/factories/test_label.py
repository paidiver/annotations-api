"""Tests for the LabelFactory, ensuring that it correctly handles related fields and label sets."""

from django.test import TestCase

from api.factories.label import LabelFactory
from api.factories.label_set import LabelSetFactory


class LabelFactoryCoverageTests(TestCase):
    """Tests for the LabelFactory, ensuring that it correctly handles related fields and label sets."""

    def test_label_with_both_label_set_id_object_reject(self) -> None:
        """Creating a Label with both label_set and label_set_id raises a ValueError."""
        with self.assertRaises(ValueError):
            LabelFactory(label_set=LabelSetFactory(), label_set_id=1)

    def test_label_uses_label_set_id(self) -> None:
        """Creating a Label with label_set_id associates it with that label set."""
        label_set = LabelSetFactory()
        label = LabelFactory(label_set_id=label_set.id)
        self.assertEqual(label.label_set_id, label_set.id)
