"""Factory for Image model."""

from __future__ import annotations

import factory

from api.models import Image

from .common_fields import CommonFieldsAllFactory, CommonFieldsImagesImageSetsFactory
from .image_set import ImageSetFactory


class ImageFactory(CommonFieldsAllFactory, CommonFieldsImagesImageSetsFactory):
    """Factory for Image."""

    class Meta:
        """Meta class for ImageFactory."""

        model = Image

    filename = factory.Sequence(lambda n: f"image_{n:06d}.jpg")
    image_set = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override creation.

        Choose between:
        - image_set (object),
        - image_set_id (raw FK),
        - or creating a new ImageSet.
        """
        image_set = kwargs.pop("image_set", None)
        image_set_id = kwargs.pop("image_set_id", None)

        if image_set is not None and image_set_id is not None:
            raise ValueError("Pass either image_set or image_set_id, not both.")

        if image_set is None and image_set_id is None:
            image_set = ImageSetFactory()

        if image_set is not None:
            kwargs["image_set"] = image_set
        else:
            kwargs["image_set_id"] = image_set_id

        return super()._create(model_class, *args, **kwargs)
