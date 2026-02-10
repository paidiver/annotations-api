"""Factory for ImageSet model."""

from __future__ import annotations

import random
from typing import Any

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

    # ImageSet-specific
    local_path = "../raw"

    # BBox fields: default None (since your model allows null/blank). This will be set by with_limits() if enabled.
    min_latitude_degrees = None
    max_latitude_degrees = None
    min_longitude_degrees = None
    max_longitude_degrees = None

    related_materials = None  # M2M, set by with_related_materials() if enabled

    @factory.post_generation
    def with_limits(self, create: bool, extracted: Any, **kwargs: Any) -> None:
        """Generate bbox limits around the latitude/longitude if extracted is True (or not provided).

        If False, leave bbox null.
        Usage:
          ImageSetFactory(with_limits=True)   # default behavior here
          ImageSetFactory(with_limits=False)  # leave bbox null

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to with_limits when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        enabled = True if extracted is None else bool(extracted)
        if not enabled:
            return

        min_lat, max_lat, min_lon, max_lon = bbox_around(self.latitude, self.longitude)
        self.min_latitude_degrees = min_lat
        self.max_latitude_degrees = max_lat
        self.min_longitude_degrees = min_lon
        self.max_longitude_degrees = max_lon
        self.save()

    @factory.post_generation
    def with_related_materials(self, create: bool, extracted: Any, **kwargs: Any) -> None:
        """Generate related materials models and assign to FKs if extracted is True (or not provided).

        Usage:
          ImageSetFactory(with_related_materials=True)
          ImageSetFactory(with_related_materials=False)  # default behavior

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to with_related_materials when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        enabled = bool(extracted) if extracted is not None else False
        if not enabled:
            return

        self.related_materials = [RelatedMaterialFactory() for _ in range(random.randint(1, 3))]
        self.save(update_fields=["context", "project", "event", "platform", "sensor", "pi", "license"])
