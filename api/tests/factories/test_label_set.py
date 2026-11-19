"""Tests for LabelSetFactory."""

from django.test import TestCase

from api.factories.label_set import LabelSetFactory


class LabelSetFactoryCoverageTests(TestCase):
    """Tests for LabelSetFactory relationships."""

    def test_with_relations_sets_named_relations(self) -> None:
        """LabelSetFactory populates named relations when enabled."""
        label_set = LabelSetFactory(with_relations=True)
        self.assertIsNotNone(label_set.context)
        self.assertIsNotNone(label_set.project)
        self.assertIsNotNone(label_set.pi)
        self.assertIsNotNone(label_set.license)

    def test_creators_and_related_materials(self) -> None:
        """LabelSetFactory creates requested creators and related materials."""
        label_set = LabelSetFactory(creators=2, related_materials=2)
        self.assertEqual(label_set.creators.count(), 2)
        self.assertEqual(label_set.related_materials.count(), 2)
