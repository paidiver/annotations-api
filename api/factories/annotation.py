"""Factory for Annotation and related models."""

import random
import uuid
from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from api.models import Annotation, AnnotationLabel, Annotator
from api.models.base import ShapeEnum

from .annotation_set import AnnotationSetFactory
from .image import ImageFactory
from .label import LabelFactory
from .utils import coords_for_shape, enum_choice


class AnnotatorFactory(DjangoModelFactory):
    """Factory for Annotator."""

    class Meta:
        """Meta class for AnnotatorFactory."""

        model = Annotator

    name = factory.LazyFunction(lambda: f"Annotator {uuid.uuid4().hex[:12]}")


class AnnotationFactory(DjangoModelFactory):
    """Factory for Annotation."""

    class Meta:
        """Meta class for AnnotationFactory."""

        model = Annotation

    class Params:
        """Factory params for controlling related object creation and M2M linking."""

        with_labels: int = 0

    annotation_platform = factory.LazyFunction(lambda: random.choice([None, "BIIGLE", "VARS", "SQUIDLE+", "custom"]))

    shape = factory.LazyFunction(lambda: enum_choice(ShapeEnum)[0])

    coordinates = factory.LazyAttribute(lambda o: coords_for_shape(o.shape))

    dimension_pixels = factory.LazyFunction(lambda: random.choice([None, random.uniform(1.0, 2000.0)]))

    image = None
    annotation_set = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        image = kwargs.pop("image", None)
        image_id = kwargs.pop("image_id", None)
        annotation_set = kwargs.pop("annotation_set", None)
        annotation_set_id = kwargs.pop("annotation_set_id", None)

        if image is not None and image_id is not None:
            raise ValueError("Pass either image or image_id, not both.")
        if annotation_set is not None and annotation_set_id is not None:
            raise ValueError("Pass either annotation_set or annotation_set_id, not both.")

        if image is None and image_id is None:
            image = ImageFactory()
        if annotation_set is None and annotation_set_id is None:
            annotation_set = AnnotationSetFactory()

        if image is not None:
            kwargs["image"] = image
        else:
            kwargs["image_id"] = image_id

        if annotation_set is not None:
            kwargs["annotation_set"] = annotation_set
        else:
            kwargs["annotation_set_id"] = annotation_set_id

        return super()._create(model_class, *args, **kwargs)


class AnnotationLabelFactory(DjangoModelFactory):
    """Factory for AnnotationLabel (through table)."""

    class Meta:
        """Meta class for AnnotationLabelFactory."""

        model = AnnotationLabel

    creation_datetime = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=random.randint(0, 3650), seconds=random.randint(0, 86400))
    )

    label = None
    annotation = None
    annotator = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override creation to handle label/annotation/annotator logic and uniqueness constraints.

        Args:
            model_class: The model class being created (AnnotationLabel).
            *args: Positional arguments (not used here).
            **kwargs: Keyword arguments for label, annotation, annotator, and their IDs.

        Returns:
            An instance of AnnotationLabel, with related fields set according to the logic.
        """
        label = kwargs.pop("label", None)
        label_id = kwargs.pop("label_id", None)
        annotation = kwargs.pop("annotation", None)
        annotation_id = kwargs.pop("annotation_id", None)
        annotator = kwargs.pop("annotator", None)
        annotator_id = kwargs.pop("annotator_id", None)

        if label is not None and label_id is not None:
            raise ValueError("Pass either label or label_id, not both.")
        if annotation is not None and annotation_id is not None:
            raise ValueError("Pass either annotation or annotation_id, not both.")
        if annotator is not None and annotator_id is not None:
            raise ValueError("Pass either annotator or annotator_id, not both.")

        if label is None and label_id is None:
            label = LabelFactory()
        if annotation is None and annotation_id is None:
            annotation = AnnotationFactory()
        if annotator is None and annotator_id is None:
            annotator = AnnotatorFactory()

        if label is not None:
            kwargs["label"] = label
        else:
            kwargs["label_id"] = label_id

        if annotation is not None:
            kwargs["annotation"] = annotation
        else:
            kwargs["annotation_id"] = annotation_id

        if annotator is not None:
            kwargs["annotator"] = annotator
        else:
            kwargs["annotator_id"] = annotator_id

        return super()._create(model_class, *args, **kwargs)
