"""Factory for AnnotationSet model."""

import random
import uuid

import factory
from factory.django import DjangoModelFactory

from api.models import AnnotationSet, AnnotationSetModel, ImageSet, LabelSet
from api.models.base import AnnotationModelEnum

from .common_fields import CommonFieldsAllFactory
from .fields import ContextFactory, LicenseFactory, PIFactory, ProjectFactory
from .image_set import ImageSetFactory
from .label_set import LabelSetFactory


class AnnotationSetFactory(CommonFieldsAllFactory):
    """Factory for AnnotationSet."""

    class Meta:
        """Factory meta class."""

        model = AnnotationSet

    name = factory.LazyFunction(lambda: f"AnnotationSet {uuid.uuid4().hex[:12]}")
    context = None
    project = None
    pi = None
    license = None

    @classmethod
    def _create(cls, model_class: type[AnnotationSet], *args, **kwargs) -> AnnotationSet:
        image_set_ids = kwargs.pop("image_set_ids", None)
        label_set_ids = kwargs.pop("label_set_ids", None)

        instance = super()._create(model_class, *args, **kwargs)

        if image_set_ids is not None:
            instance.image_sets.set(ImageSet.objects.filter(id__in=image_set_ids))
        if label_set_ids is not None:
            instance.label_sets.set(LabelSet.objects.filter(id__in=label_set_ids))

        return instance

    @factory.post_generation
    def with_relations(self, create: bool, extracted: bool, **kwargs) -> None:
        """Generate related objects and set FKs if with_relations is True.

        Usage:
            AnnotationSetFactory(with_relations=True)  # creates and sets all related fields
            AnnotationSetFactory(with_relations=False) # leaves all related fields null

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to with_relations when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        enabled = bool(extracted) if extracted is not None else False
        if not enabled:
            return

        self.context = ContextFactory()
        self.project = ProjectFactory()
        self.pi = PIFactory()
        self.license = LicenseFactory()
        self.save(update_fields=["context", "project", "pi", "license"])

    @factory.post_generation
    def image_sets(self, create: bool, extracted: bool, **kwargs) -> None:
        """Generate related image sets via AnnotationSetImageSet if image_sets > 0.

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to image_sets when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        through_model = self.image_sets.through

        fk_to_self_name = None
        for f in through_model._meta.fields:
            if getattr(f, "remote_field", None) and f.remote_field.model == self.__class__:
                fk_to_self_name = f.name
                break
        if fk_to_self_name is None:
            raise RuntimeError(f"Could not find FK from {through_model.__name__} to {self.__class__.__name__}")

        if extracted is None:
            return

        if isinstance(extracted, int):
            if extracted <= 0:
                return
            image_sets_list = [ImageSetFactory() for _ in range(extracted)]
        else:
            image_sets_list = list(extracted)
        rows = [through_model(**{fk_to_self_name: self, "image_set": c}) for c in image_sets_list]
        through_model.objects.bulk_create(rows, ignore_conflicts=True)

    @factory.post_generation
    def label_sets(self, create: bool, extracted: bool, **kwargs) -> None:
        """Populate label sets from a count or iterable."""
        if not create or extracted is None:
            return
        if isinstance(extracted, int):
            label_sets = [LabelSetFactory() for _ in range(max(extracted, 0))]
        else:
            label_sets = list(extracted)
        self.label_sets.set(label_sets)


class AnnotationSetModelFactory(DjangoModelFactory):
    """Factory for AnnotationSetModel."""

    class Meta:
        """Factory meta class."""

        model = AnnotationSetModel

    annotation_set = factory.SubFactory(AnnotationSetFactory)
    model_id = factory.LazyFunction(lambda: f"model-{uuid.uuid4().hex[:12]}")
    name = factory.LazyFunction(lambda: f"Model {uuid.uuid4().hex[:12]}")
    version = factory.Iterator(["1.0", "1.1", "2.0"], cycle=True)
    task = factory.Iterator([item.value for item in AnnotationModelEnum], cycle=True)
    handle = factory.LazyFunction(lambda: f"https://example.org/models/{uuid.uuid4()}")
    weights_sha256 = factory.LazyFunction(lambda: uuid.uuid4().hex + uuid.uuid4().hex)
    score_type = "probability"
    confidence_threshold = factory.LazyFunction(lambda: random.uniform(0.0, 1.0))

    @classmethod
    def _create(cls, model_class: type[AnnotationSetModel], *args, **kwargs) -> AnnotationSetModel:
        instance = super()._create(model_class, *args, **kwargs)
        if instance.label_set_id is not None:
            instance.annotation_set.label_sets.add(instance.label_set)
        return instance
