"""Tests for the AnnotationSetFactory, ensuring that it correctly handles related fields and image sets."""

from django.test import TestCase

from api.factories.annotation_set import AnnotationSetFactory
from api.factories.fields import CreatorFactory
from api.factories.image_set import ImageSetFactory


class AnnotationSetFactoryCoverageTests(TestCase):
    """Tests for the AnnotationSetFactory, ensuring that it correctly handles related fields and image sets."""

    def test_with_relations_does_nothing_on_build(self):
        """Test that building an AnnotationSetFactory with with_relations=True does not set related fields."""
        aset = AnnotationSetFactory.build(with_relations=True)
        self.assertIsNone(aset.context)
        self.assertIsNone(aset.project)
        self.assertIsNone(aset.pi)
        self.assertIsNone(aset.license)

    def test_with_relations_does_nothing_when_disabled(self):
        """Test that creating an AnnotationSetFactory with with_relations=False does not set related fields."""
        aset = AnnotationSetFactory(with_relations=False)
        self.assertIsNone(aset.context)
        self.assertIsNone(aset.project)
        self.assertIsNone(aset.pi)
        self.assertIsNone(aset.license)

    def test_with_relations_sets_all_related_fields_when_enabled(self):
        """Test that creating an AnnotationSetFactory with with_relations=True sets all related fields."""
        aset = AnnotationSetFactory(with_relations=True)
        self.assertIsNotNone(aset.context)
        self.assertIsNotNone(aset.project)
        self.assertIsNotNone(aset.pi)
        self.assertIsNotNone(aset.license)

    def test_creators_when_enabled(self):
        """Test that creating an AnnotationSetFactory with a list of creators sets those creators on the instance."""
        creator = CreatorFactory()
        aset = AnnotationSetFactory(creators=[creator])
        self.assertIn(creator, aset.creators.all())

    def test_creators_equal0(self):
        """Test that creating an AnnotationSetFactory with creators=0 results in no creators being associated."""
        aset = AnnotationSetFactory(creators=0)
        self.assertEqual(aset.creators.count(), 0)

    def test_image_sets_uses_extracted_list(self):
        """Test that creating an AnnotationSet with a list of image sets associates the image sets with the instance."""
        aset = AnnotationSetFactory()
        img1 = ImageSetFactory()
        img2 = ImageSetFactory()

        aset = AnnotationSetFactory(image_sets=[img1, img2])

        ids = set(aset.image_sets.values_list("id", flat=True))
        self.assertEqual(ids, {img1.id, img2.id})

    def test_image_sets_uses_image_sets_count_when_no_extracted(self):
        """AnnotationSet with image_sets set to an integer associates that many image sets with the instance."""
        aset = AnnotationSetFactory(image_sets=3)
        self.assertEqual(aset.image_sets.count(), 3)

        aset = AnnotationSetFactory(image_sets=0)
        self.assertEqual(aset.image_sets.count(), 0)

    def test_image_sets_raises_runtimeerror_when_fk_to_self_not_found(self):
        """Creating an AnnotationSet with image_sets specified raises a RuntimeError."""
        aset = AnnotationSetFactory()

        through_model = aset.image_sets.through

        original_fields = through_model._meta.fields

        class DummyRemoteField:
            model = object

        class DummyField:
            name = "not_fk"
            remote_field = DummyRemoteField()

        try:
            through_model._meta.fields = [DummyField()]
            with self.assertRaises(RuntimeError):
                AnnotationSetFactory(image_sets=[ImageSetFactory()])
        finally:
            through_model._meta.fields = original_fields
