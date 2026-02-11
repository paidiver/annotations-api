"""Tests for the ImageSetFactory, ensuring that it correctly handles related fields and image sets."""

from django.test import TestCase

from api.factories.fields import RelatedMaterialFactory
from api.factories.image import ImageFactory
from api.factories.image_set import ImageSetFactory


class ImageImageSetFactoryCoverageTests(TestCase):
    """Tests for the ImageSetFactory, ensuring that it correctly handles related fields and image sets."""

    def test_with_relations_does_nothing_on_build(self):
        """Test that building an ImageSetFactory with with_relations=True does not set related fields."""
        aset = ImageSetFactory.build(with_relations=True)
        self.assertIsNone(aset.context)
        self.assertIsNone(aset.project)
        self.assertIsNone(aset.pi)
        self.assertIsNone(aset.license)

    def test_with_relations_does_nothing_when_disabled(self):
        """Test that creating an ImageSetFactory with with_relations=False does not set related fields."""
        aset = ImageSetFactory(with_relations=False)
        self.assertIsNone(aset.context)
        self.assertIsNone(aset.project)
        self.assertIsNone(aset.pi)
        self.assertIsNone(aset.license)

    def test_with_relations_sets_all_related_fields_when_enabled(self):
        """Test that creating an ImageSetFactory with with_relations=True sets all related fields."""
        aset = ImageSetFactory(with_relations=True)
        self.assertIsNotNone(aset.context)
        self.assertIsNotNone(aset.project)
        self.assertIsNotNone(aset.pi)
        self.assertIsNotNone(aset.license)

    def test_related_materials_when_enabled(self):
        """Creating an ImageSetFactory with a list of related materials sets those related materials on the instance."""
        related_material = RelatedMaterialFactory()
        aset = ImageSetFactory(related_materials=[related_material])
        self.assertIn(related_material, aset.related_materials.all())

    def test_related_materials_equal0(self):
        """Creating an ImageSetFactory with related_materials=0 results in no related materials being associated."""
        aset = ImageSetFactory(related_materials=0)
        self.assertEqual(aset.related_materials.count(), 0)

    def test_image_with_both_image_set_id_and_image_set_reject(self):
        """Creating an Image with both image_set and image_set_id raises a ValueError."""
        with self.assertRaises(ValueError):
            ImageFactory(image_set=ImageSetFactory(), image_set_id=1)
