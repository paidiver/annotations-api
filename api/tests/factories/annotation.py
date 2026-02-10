"""Factory for Annotation and related models."""

from __future__ import annotations

import random
from datetime import timedelta
from typing import Any

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from api.models import Annotation, AnnotationLabel, Annotator

from .annotation_set import AnnotationSetFactory
from .image import ImageFactory
from .label import LabelFactory
from .utils import coords_for_shape, pick_choice


class AnnotatorFactory(DjangoModelFactory):
    """Factory for Annotator."""

    class Meta:
        """Meta class for AnnotatorFactory."""

        model = Annotator

    name = factory.Sequence(lambda n: f"Annotator {n:05d}")


class AnnotationFactory(DjangoModelFactory):
    """Factory for Annotation.

    Relationship behavior:
      - If `image` provided -> use it
      - Else if `image_id` provided -> use it (no Image created)
      - Else -> create Image via ImageFactory

    And similarly for annotation_set / annotation_set_id.

    You can also opt-in to creating labels via:
      AnnotationFactory(with_labels=3)
    """

    class Meta:
        """Meta class for AnnotationFactory."""

        model = Annotation

    class Params:
        """Factory params for controlling related object creation and M2M linking."""

        with_labels: int = 0  # create N AnnotationLabel rows

    annotation_platform = factory.LazyFunction(lambda: random.choice([None, "BIIGLE", "VARS", "SQUIDLE+", "custom"]))

    # Pick a valid choice from the model's `shape` choices
    shape = factory.LazyAttribute(lambda o: pick_choice(Annotation, "shape"))

    # Coordinates consistent with shape
    coordinates = factory.LazyAttribute(lambda o: coords_for_shape(o.shape))

    dimension_pixels = factory.LazyFunction(lambda: random.choice([None, random.uniform(1.0, 2000.0)]))

    # Set in _create() to avoid unnecessary subfactory creation
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

    @factory.post_generation
    def labels(self, create: bool, extracted: Any, **kwargs: Any) -> None:
        """Generate related labels via AnnotationLabelFactory if with_labels > 0."""
        if not create:
            return

        n = int(getattr(self, "with_labels", 0) or 0)
        if n <= 0:
            return

        # Create labels attached to same annotation_set for consistency
        labels = [LabelFactory(annotation_set=self.annotation_set) for _ in range(n)]
        # Annotator optional; often None
        for lbl in labels:
            AnnotationLabelFactory(annotation=self, label=lbl)


class AnnotationLabelFactory(DjangoModelFactory):
    """Factory for AnnotationLabel (through table).

    Relationship behavior:
      - Accepts label or label_id
      - Accepts annotation or annotation_id
      - Accepts annotator or annotator_id (optional; if neither provided, defaults to None)
    """

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

        if label is not None:
            kwargs["label"] = label
        else:
            kwargs["label_id"] = label_id

        if annotation is not None:
            kwargs["annotation"] = annotation
        else:
            kwargs["annotation_id"] = annotation_id

        # annotator is optional: default None unless provided or you want a default
        if annotator is not None:
            kwargs["annotator"] = annotator
        elif annotator_id is not None:
            kwargs["annotator_id"] = annotator_id
        else:
            kwargs["annotator"] = None

        return super()._create(model_class, *args, **kwargs)
