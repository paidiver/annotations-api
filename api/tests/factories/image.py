"""Factory for Image model."""

import uuid

import factory

from api.models import Image

from .common_fields import CommonFieldsAllFactory, CommonFieldsImagesImageSetsFactory
from .image_set import ImageSetFactory


class ImageFactory(CommonFieldsAllFactory, CommonFieldsImagesImageSetsFactory):
    """Factory for Image."""

    class Params:
        """Factory params for controlling related object creation and M2M linking."""

        with_creators: bool = False
        with_relations: bool = False

    class Meta:
        """Meta class for ImageFactory."""

        model = Image

    filename = factory.LazyFunction(lambda: f"image_{uuid.uuid4().hex[:12]}.jpg")
    image_set = None

    @classmethod
    def _create(cls, model_class: type[Image], *args, **kwargs) -> Image:
        """Override creation to handle image_set / image_set_id logic.

        Args:
            model_class: The Image model class.
            *args: Positional arguments for the model creation.
            **kwargs: Keyword arguments for the model creation.

        Returns:
            An instance of the Image model.
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
