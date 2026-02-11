"""Tests for error handling in Annotation-related factories."""

from django.test import TestCase

from api.factories.annotation import (
    AnnotationFactory,
    AnnotationLabelFactory,
    AnnotatorFactory,
)
from api.factories.annotation_set import AnnotationSetFactory
from api.factories.image import ImageFactory
from api.factories.label import LabelFactory


class AnnotationFactoriesErrorTests(TestCase):
    """Tests for error handling in Annotation-related factories."""

    def test_annotation_factory_creation_with_image_id_annotation_set_id(self):
        """Test that AnnotationFactory can create an annotation when image_id and annotation_set_id are provided."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()
        annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id)
        self.assertEqual(annotation.image_id, image.id)
        self.assertEqual(annotation.annotation_set_id, annotation_set.id)

    def test_annotation_factory_creation_with_several_shapes(self):
        """Test that AnnotationFactory can create annotations with different shapes."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()

        annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id, shape="whole-image")
        self.assertEqual(annotation.shape, "whole-image")

        annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id, shape="rectangle")
        self.assertEqual(annotation.shape, "rectangle")

        annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id, shape="single-pixel")
        self.assertEqual(annotation.shape, "single-pixel")

        annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id, shape="ellipse")
        self.assertEqual(annotation.shape, "ellipse")

        annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id, shape="polygon")
        self.assertEqual(annotation.shape, "polygon")

    def test_annotation_factory_creation_with_wrong_shape(self):
        """Test that AnnotationFactory raises a ValueError when an invalid shape is provided."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()
        with self.assertRaisesMessage(ValueError, "Unknown shape: invalid-shape"):
            AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id, shape="invalid-shape")

    def test_annotation_factory_raises_if_image_and_image_id_both_passed(self):
        """Test that AnnotationFactory raises a ValueError when both image and image_id are provided."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()

        with self.assertRaisesMessage(ValueError, "Pass either image or image_id, not both."):
            AnnotationFactory(image=image, image_id=image.id, annotation_set=annotation_set)

    def test_annotation_factory_raises_if_annotation_set_and_annotation_set_id_both_passed(self):
        """Test that AnnotationFactory raises a ValueError when both annotation_set and _id are provided."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()

        with self.assertRaisesMessage(ValueError, "Pass either annotation_set or annotation_set_id, not both."):
            AnnotationFactory(image=image, annotation_set=annotation_set, annotation_set_id=annotation_set.id)

    def test_annotation_label_factory_raises_if_label_and_label_id_both_passed(self):
        """Test that AnnotationLabelFactory raises a ValueError when both label and label_id are provided."""
        label = LabelFactory()
        annotation = AnnotationFactory()

        with self.assertRaisesMessage(ValueError, "Pass either label or label_id, not both."):
            AnnotationLabelFactory(label=label, label_id=label.id, annotation=annotation)

    def test_annotation_label_factory_raises_if_annotation_and_annotation_id_both_passed(self):
        """Test that AnnotationLabelFactory raises a ValueError when both annotation and annotation_id are provided."""
        label = LabelFactory()
        annotation = AnnotationFactory()

        with self.assertRaisesMessage(ValueError, "Pass either annotation or annotation_id, not both."):
            AnnotationLabelFactory(label=label, annotation=annotation, annotation_id=annotation.id)

    def test_annotation_label_factory_raises_if_annotator_and_annotator_id_both_passed(self):
        """Test that AnnotationLabelFactory raises a ValueError when both annotator and annotator_id are provided."""
        label = LabelFactory()
        annotation = AnnotationFactory()
        annotator = AnnotatorFactory()

        with self.assertRaisesMessage(ValueError, "Pass either annotator or annotator_id, not both."):
            AnnotationLabelFactory(
                label=label,
                annotation=annotation,
                annotator=annotator,
                annotator_id=annotator.id,
            )

    def test_annotation_label_factory_creation(self):
        """Test that AnnotationLabelFactory can create annotation labels with different combinations of inputs."""
        image = ImageFactory()
        annotation_set = AnnotationSetFactory()
        annotation = AnnotationFactory(image_id=image.id, annotation_set_id=annotation_set.id)
        label = LabelFactory(annotation_set_id=annotation_set.id)
        annotator = AnnotatorFactory()
        annotation_label = AnnotationLabelFactory(label=label, annotation=annotation, annotator=annotator)

        self.assertEqual(annotation_label.label_id, label.id)
        self.assertEqual(annotation_label.annotation_id, annotation.id)
        self.assertEqual(annotation_label.annotator_id, annotator.id)

        label_2 = LabelFactory(annotation_set_id=annotation_set.id)
        annotation_label_2 = AnnotationLabelFactory(
            label_id=label_2.id, annotation_id=annotation.id, annotator_id=annotator.id
        )
        self.assertEqual(annotation_label_2.annotation_id, annotation.id)
        self.assertEqual(annotation_label_2.annotator_id, annotator.id)
        self.assertEqual(annotation_label_2.label_id, label_2.id)

        annotation_label_3 = AnnotationLabelFactory()
        self.assertNotEqual(annotation_label_3.label_id, label_2.id)
        self.assertNotEqual(annotation_label_3.annotation_id, annotation.id)
        self.assertNotEqual(annotation_label_3.annotator_id, annotator.id)
