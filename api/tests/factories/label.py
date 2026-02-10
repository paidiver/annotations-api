"""Factory for Label model."""

from __future__ import annotations

import random

import factory
from factory.django import DjangoModelFactory

from api.models import Label

# You should have / create this similarly to ImageSetFactory / etc.
from .annotation_set import AnnotationSetFactory


class LabelFactory(DjangoModelFactory):
    """Factory for Label.

    Relationship behavior:
      - If `annotation_set` is provided: use it.
      - Else if `annotation_set_id` is provided: use it (no AnnotationSet created).
      - Else: create a new AnnotationSet via AnnotationSetFactory.

    Notes:
      - `name` is unique, so we use a Sequence.
      - `parent_label_name` is required (no null/blank), so we always fill it.
    """

    class Meta:
        """Factory meta class."""

        model = Label

    # Unique label name (BIIGLE-style names can be anything; keep it simple)
    name = factory.Sequence(lambda n: f"Label {n:05d}")

    # Required
    parent_label_name = factory.LazyFunction(
        lambda: random.choice(["Root", "Biota", "Animalia", "Plantae", "Fungi", "Other"])
    )

    # Optional taxonomy fields
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

    lowest_aphia_id = factory.LazyFunction(
        lambda: None if random.random() < 0.7 else str(random.randint(10000, 9999999))  # noqa: PLR2004
    )

    name_is_lowest = factory.LazyFunction(lambda: random.random() < 0.3)  # noqa: PLR2004

    identification_qualifier = factory.LazyFunction(
        lambda: random.choice([None, "cf.", "aff.", "sp.", "gen. sp.", "indet."])
    )

    # We'll set annotation_set / annotation_set_id in _create()
    annotation_set = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
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
