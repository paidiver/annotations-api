"""Factory for Annotation and related models."""

import random
from datetime import timedelta

import factory
from django.db import models
from django.utils import timezone
from factory.django import DjangoModelFactory

from api.models import Annotation, AnnotationSet, Image, Label
from api.models.base import ShapeEnum

from .annotation_set import AnnotationSetFactory
from .image import ImageFactory
from .label import LabelFactory
from .utils import coords_for_shape


def _resolve_relation(
    kwargs: dict, field_name: str, model_class: type[models.Model], factory_class: type
) -> models.Model:
    """Resolve a factory relation supplied as an object or primary key."""
    instance = kwargs.pop(field_name, None)
    instance_id = kwargs.pop(f"{field_name}_id", None)
    if instance is not None and instance_id is not None:
        raise ValueError(f"Pass either {field_name} or {field_name}_id, not both.")
    if instance is not None:
        return instance
    if instance_id is not None:
        return model_class.objects.get(pk=instance_id)
    return factory_class()


class AnnotationFactory(DjangoModelFactory):
    """Factory for Annotation."""

    class Meta:
        """Meta class for AnnotationFactory."""

        model = Annotation

    annotation_platform = factory.LazyFunction(lambda: random.choice([None, "BIIGLE", "VARS", "SQUIDLE+", "custom"]))

    shape = factory.Iterator([e.value for e in ShapeEnum], cycle=True)

    coordinates = factory.LazyAttribute(lambda o: coords_for_shape(o.shape))

    dimension_pixels = factory.LazyFunction(lambda: random.choice([None, random.uniform(1.0, 2000.0)]))

    creation_datetime = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=random.randint(0, 3650), seconds=random.randint(0, 86400))
    )
    human_or_machine = "human"
    mask = factory.LazyAttribute(
        lambda obj: {"encoding": "coco-rle", "width": 4000, "height": 3000, "counts": []}
        if obj.shape == "mask"
        else None
    )

    image = None
    annotation_set = None
    label = None
    creator = None

    @classmethod
    def _create(cls, model_class: type[Annotation], *args, **kwargs) -> Annotation:
        image = _resolve_relation(kwargs, "image", Image, ImageFactory)
        annotation_set = _resolve_relation(kwargs, "annotation_set", AnnotationSet, AnnotationSetFactory)
        label = _resolve_relation(kwargs, "label", Label, LabelFactory)

        annotation_set.label_sets.add(label.label_set)
        kwargs["image"] = image
        kwargs["annotation_set"] = annotation_set
        kwargs["label"] = label

        return super()._create(model_class, *args, **kwargs)
