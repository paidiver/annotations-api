"""Factory for ImageSet model."""

import uuid

import factory

from api.models import ImageSet

from .common_fields import CommonFieldsAllFactory, CommonFieldsImagesImageSetsFactory
from .fields import (
    RelatedMaterialFactory,
)
from .utils import bbox_around


class ImageSetFactory(CommonFieldsAllFactory, CommonFieldsImagesImageSetsFactory):
    """Creates ImageSet with geo fields."""

    class Meta:
        """Factory meta class."""

        model = ImageSet

    name = factory.LazyFunction(lambda: f"ImageSet {uuid.uuid4().hex[:12]}")

    local_path = "../raw"

    min_latitude_degrees = None
    max_latitude_degrees = None
    min_longitude_degrees = None
    max_longitude_degrees = None

    related_materials = None

    @factory.post_generation
    def with_limits(self, create: bool, extracted, **kwargs) -> None:
        """Populate bbox fields if with_limits is True.

        Usage:
            ImageSetFactory(with_limits=True)  # sets bbox fields based on latitude/longitude
            ImageSetFactory(with_limits=False) # leaves bbox fields null

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to with_limits when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        enabled = bool(extracted) if extracted is not None else False
        if not enabled:
            return

        min_lat, max_lat, min_lon, max_lon = bbox_around(self.latitude, self.longitude)
        self.min_latitude_degrees = min_lat
        self.max_latitude_degrees = max_lat
        self.min_longitude_degrees = min_lon
        self.max_longitude_degrees = max_lon
        self.save(
            update_fields=[
                "min_latitude_degrees",
                "max_latitude_degrees",
                "min_longitude_degrees",
                "max_longitude_degrees",
            ]
        )

    @factory.post_generation
    def related_materials(self, create: bool, extracted, **kwargs) -> None:
        """Populate related_materials M2M via the through model.

        Usage;
            ImageSetFactory(related_materials=[related_material1, related_material2])
            ImageSetFactory(related_materials=3)

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to related_materials when the factory is called (list of related materials).
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        through_model = self.related_materials.through

        fk_to_self_name = None
        for f in through_model._meta.fields:
            if getattr(f, "remote_field", None) and f.remote_field.model == self.__class__:
                fk_to_self_name = f.name
                break

        if extracted is None:
            return

        if isinstance(extracted, int):
            if extracted <= 0:
                return
            related_materials_list = [RelatedMaterialFactory() for _ in range(extracted)]
        else:
            related_materials_list = list(extracted)
        rows = [through_model(**{fk_to_self_name: self, "related_material": c}) for c in related_materials_list]
        through_model.objects.bulk_create(rows, ignore_conflicts=True)
