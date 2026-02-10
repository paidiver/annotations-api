"""Factory for AnnotationSet model."""

from __future__ import annotations

import random
from typing import Any

import factory
from factory.django import DjangoModelFactory

from api.models import AnnotationSet, AnnotationSetCreator, AnnotationSetImageSet

from .common_fields import CommonFieldsAllFactory
from .fields import (
    ContextFactory,
    CreatorFactory,
    LicenseFactory,
    PIFactory,
    ProjectFactory,
)
from .image_set import ImageSetFactory


class AnnotationSetFactory(CommonFieldsAllFactory):
    """Factory for AnnotationSet.

    Default:
      - creates an AnnotationSet with no optional FK relations and no M2M links.

    Opt-in behaviors:
      - AnnotationSetFactory(with_relations=True)
      - AnnotationSetFactory(with_creators=3)
      - AnnotationSetFactory(with_image_sets=2)

    You can also pass explicit lists:
      - AnnotationSetFactory(creators_list=[c1, c2])
      - AnnotationSetFactory(image_sets_list=[iset1, iset2])
    """

    class Meta:
        """Factory meta class."""

        model = AnnotationSet

    version = factory.LazyFunction(lambda: random.choice([None, "v1", "v1.0", "v2", "2024-01", "draft"]))

    context = None
    project = None
    pi = None
    license = None

    class Params:
        """Factory params for controlling related object creation and M2M linking."""

        with_relations: bool = False
        with_creators: int = 0
        with_image_sets: int = 0
        creators_list: list[Any] | None = None
        image_sets_list: list[Any] | None = None

    @factory.post_generation
    def apply_relations(self, create: bool, extracted: Any, **kwargs: Any) -> None:
        """Generate related models and assign to FKs if with_relations is True.

        This runs before the specific with_camera_models to ensure camera-related fields are populated
        if that is also enabled.

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to with_relations when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        if not self.with_relations:
            return

        self.context = ContextFactory()
        self.project = ProjectFactory()
        self.pi = PIFactory()
        self.license = LicenseFactory()
        self.save(update_fields=["context", "project", "pi", "license"])

    @factory.post_generation
    def creators(self, create: bool, extracted: Any, **kwargs: Any) -> None:
        """Populate M2M creators via through model.

        - If creators_list is provided, use it.
        - Else if with_creators > 0, create that many creators.
        """
        if not create:
            return

        creators_list = self.creators_list
        if creators_list is None:
            n = int(self.with_creators or 0)
            if n <= 0:
                return
            creators_list = [CreatorFactory() for _ in range(n)]

        AnnotationSetCreator.objects.bulk_create(
            [AnnotationSetCreator(annotation_set=self, creator=c) for c in creators_list],
            ignore_conflicts=True,
        )

    @factory.post_generation
    def image_sets(self, create: bool, extracted: Any, **kwargs: Any) -> None:
        """Populate M2M image_sets via through model.

        - If image_sets_list is provided, use it.
        - Else if with_image_sets > 0, create that many ImageSets.
        """
        if not create:
            return

        image_sets_list = self.image_sets_list
        if image_sets_list is None:
            n = int(self.with_image_sets or 0)
            if n <= 0:
                return
            image_sets_list = [ImageSetFactory() for _ in range(n)]

        AnnotationSetImageSet.objects.bulk_create(
            [AnnotationSetImageSet(annotation_set=self, image_set=iset) for iset in image_sets_list],
            ignore_conflicts=True,
        )


class AnnotationSetCreatorFactory(DjangoModelFactory):
    """Through-table factory.

    Relationship behavior:
      - If `annotation_set` provided, use it.
      - Else if `annotation_set_id` provided, use it.
      - Else create one.

    Same for creator.
    """

    class Meta:
        """Meta class for AnnotationSetCreatorFactory."""

        model = AnnotationSetCreator

    annotation_set = None
    creator = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        annotation_set = kwargs.pop("annotation_set", None)
        annotation_set_id = kwargs.pop("annotation_set_id", None)
        creator = kwargs.pop("creator", None)
        creator_id = kwargs.pop("creator_id", None)

        if annotation_set is not None and annotation_set_id is not None:
            raise ValueError("Pass either annotation_set or annotation_set_id, not both.")
        if creator is not None and creator_id is not None:
            raise ValueError("Pass either creator or creator_id, not both.")

        if annotation_set is None and annotation_set_id is None:
            annotation_set = AnnotationSetFactory()
        if creator is None and creator_id is None:
            creator = CreatorFactory()

        if annotation_set is not None:
            kwargs["annotation_set"] = annotation_set
        else:
            kwargs["annotation_set_id"] = annotation_set_id

        if creator is not None:
            kwargs["creator"] = creator
        else:
            kwargs["creator_id"] = creator_id

        return super()._create(model_class, *args, **kwargs)


class AnnotationSetImageSetFactory(DjangoModelFactory):
    """Through-table factory linking AnnotationSet <-> ImageSet.

    Supports passing either objects or raw ids.
    """

    class Meta:
        """Meta class for AnnotationSetImageSetFactory."""

        model = AnnotationSetImageSet

    annotation_set = None
    image_set = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        annotation_set = kwargs.pop("annotation_set", None)
        annotation_set_id = kwargs.pop("annotation_set_id", None)
        image_set = kwargs.pop("image_set", None)
        image_set_id = kwargs.pop("image_set_id", None)

        if annotation_set is not None and annotation_set_id is not None:
            raise ValueError("Pass either annotation_set or annotation_set_id, not both.")
        if image_set is not None and image_set_id is not None:
            raise ValueError("Pass either image_set or image_set_id, not both.")

        if annotation_set is None and annotation_set_id is None:
            annotation_set = AnnotationSetFactory()
        if image_set is None and image_set_id is None:
            image_set = ImageSetFactory()

        if annotation_set is not None:
            kwargs["annotation_set"] = annotation_set
        else:
            kwargs["annotation_set_id"] = annotation_set_id

        if image_set is not None:
            kwargs["image_set"] = image_set
        else:
            kwargs["image_set_id"] = image_set_id

        return super()._create(model_class, *args, **kwargs)
