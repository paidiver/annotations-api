"""Factory for AnnotationSet model."""

import random
import uuid

import factory

from api.models import AnnotationSet

from .common_fields import CommonFieldsAllFactory
from .fields import ContextFactory, LicenseFactory, PIFactory, ProjectFactory
from .image_set import ImageSetFactory


class AnnotationSetFactory(CommonFieldsAllFactory):
    """Factory for AnnotationSet."""

    class Meta:
        """Factory meta class."""

        model = AnnotationSet

    name = factory.LazyFunction(lambda: f"AnnotationSet {uuid.uuid4().hex[:12]}")
    version = factory.LazyFunction(lambda: random.choice([None, "v1", "v1.0", "v2", "2024-01", "draft"]))

    context = None
    project = None
    pi = None
    license = None

    class Params:
        """Factory params for controlling related object creation and M2M linking."""

        image_set_ids: list[int] | None = None

    @factory.post_generation
    def with_relations(self, create: bool, extracted, **kwargs) -> None:
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
    def image_sets(self, create: bool, extracted, **kwargs) -> None:
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
