"""Tests for error handling in Annotation-related factories."""

from django.test import TestCase

from api.factories.annotation import AnnotationFactory
from api.factories.annotation_set import AnnotationSetFactory
from api.factories.fields import CreatorFactory
from api.factories.image import ImageFactory
from api.factories.label import LabelFactory


class AnnotationFactoriesErrorTests(TestCase):
    """Tests for error handling in Annotation-related factories."""

    def test_annotation_factory_creation_with_image_id_annotation_set_id(self) -> None:
        """Test that AnnotationFactory can create an annotation when image_id and annotation_set_id are provided."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()
        annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id)
        self.assertEqual(annotation.image_id, image.id)
        self.assertEqual(annotation.annotation_set_id, annotation_set.id)

    def test_annotation_factory_creation_with_several_shapes(self) -> None:
        """Test that AnnotationFactory can create annotations with different shapes."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()
        shapes = [
            "whole-image",
            "rectangle",
            "single-pixel",
            "ellipse",
            "polygon",
            "polyline",
            "circle",
            "centrexy",
            "mask",
        ]
        for shape in shapes:
            annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id, shape=shape)
            self.assertEqual(annotation.shape, shape)

    def test_annotation_factory_creation_with_wrong_shape(self) -> None:
        """Test that AnnotationFactory raises a ValueError when an invalid shape is provided."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()
        with self.assertRaisesMessage(ValueError, "Unknown shape: invalid-shape"):
            AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id, shape="invalid-shape")

    def test_annotation_factory_raises_if_image_and_image_id_both_passed(self) -> None:
        """Test that AnnotationFactory raises a ValueError when both image and image_id are provided."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()

        with self.assertRaisesMessage(ValueError, "Pass either image or image_id, not both."):
            AnnotationFactory(image=image, image_id=image.id, annotation_set=annotation_set)

    def test_annotation_factory_raises_if_annotation_set_and_annotation_set_id_both_passed(self) -> None:
        """Test that AnnotationFactory raises a ValueError when both annotation_set and _id are provided."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()

        with self.assertRaisesMessage(ValueError, "Pass either annotation_set or annotation_set_id, not both."):
            AnnotationFactory(image=image, annotation_set=annotation_set, annotation_set_id=annotation_set.id)

    def test_annotation_factory_raises_if_label_and_label_id_both_passed(self) -> None:
        """Test that AnnotationFactory raises a ValueError when both label and label_id are provided."""
        label = LabelFactory()

        with self.assertRaisesMessage(ValueError, "Pass either label or label_id, not both."):
            AnnotationFactory(label=label, label_id=label.id)

    def test_annotation_factory_sets_label_and_creator(self) -> None:
        """Test that AnnotationFactory sets the direct label and annotation creator."""
        label = LabelFactory()
        creator = CreatorFactory()
        annotation_set = AnnotationSetFactory()
        annotation = AnnotationFactory(
            annotation_set=annotation_set,
            label=label,
            creator=creator,
        )

        self.assertEqual(annotation.label_id, label.id)
        self.assertIn(label.label_set, annotation_set.label_sets.all())
        self.assertEqual(annotation.creator, creator)
