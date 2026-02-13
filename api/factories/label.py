"""Factory for Label model."""

import random
import uuid

import factory
from factory.django import DjangoModelFactory

from api.models import Label

from .annotation_set import AnnotationSetFactory


class LabelFactory(DjangoModelFactory):
    """Factory for Label."""

    class Meta:
        """Factory meta class."""

        model = Label

    name = factory.LazyFunction(lambda: f"Label {uuid.uuid4().hex[:12]}")

    parent_label_name = factory.LazyFunction(
        lambda: random.choice(["Root", "Biota", "Animalia", "Plantae", "Fungi", "Other"])
    )

    lowest_taxonomic_name = factory.LazyFunction(
        lambda: random.choice(
            [
                None,
                "Porifera",
                "Cnidaria",
                "Echinodermata",
                "Arthropoda",
                "Chordata",
                "Phaeophyceae",
            ]
        )
    )

    lowest_aphia_id = factory.LazyFunction(lambda: str(random.randint(1, 9999)))

    name_is_lowest = factory.LazyFunction(lambda: random.random() < 0.3)  # noqa: PLR2004

    identification_qualifier = factory.LazyFunction(
        lambda: random.choice([None, "cf.", "aff.", "sp.", "gen. sp.", "indet."])
    )

    annotation_set = None

    @classmethod
    def _create(cls, model_class: type[Label], *args, **kwargs) -> Label:
        """Override creation to handle annotation_set / annotation_set_id logic.

        Args:
            model_class: The model class being created (Label).
            *args: Positional arguments (not used here).
            **kwargs: Keyword arguments

        Returns:
            An instance of Label, with annotation_set set according to the logic.
        """
        annotation_set = kwargs.pop("annotation_set", None)
        annotation_set_id = kwargs.pop("annotation_set_id", None)

        if annotation_set is not None and annotation_set_id is not None:
            raise ValueError("Pass either annotation_set or annotation_set_id, not both.")

        if annotation_set is None and annotation_set_id is None:
            annotation_set = AnnotationSetFactory()

        if annotation_set is not None:
            kwargs["annotation_set"] = annotation_set
        else:
            kwargs["annotation_set_id"] = annotation_set_id

        return super()._create(model_class, *args, **kwargs)
