"""Factory for LabelSet model."""

import uuid

import factory

from api.models import LabelSet

from .common_fields import CommonFieldsAllFactory
from .fields import ContextFactory, LicenseFactory, PIFactory, ProjectFactory, RelatedMaterialFactory


class LabelSetFactory(CommonFieldsAllFactory):
    """Factory for LabelSet."""

    class Meta:
        """Factory meta class."""

        model = LabelSet

    name = factory.LazyFunction(lambda: f"LabelSet {uuid.uuid4().hex[:12]}")
    catalogue = factory.LazyFunction(lambda: f"https://example.org/catalogue/{uuid.uuid4()}")
    funding = factory.Faker("sentence")

    context = None
    project = None
    pi = None
    license = None

    @factory.post_generation
    def with_relations(self, create: bool, extracted: bool, **kwargs) -> None:
        """Generate related objects when with_relations is True."""
        if not create or not extracted:
            return

        self.context = ContextFactory()
        self.project = ProjectFactory()
        self.pi = PIFactory()
        self.license = LicenseFactory()
        self.save(update_fields=["context", "project", "pi", "license"])

    @factory.post_generation
    def related_materials(self, create: bool, extracted: bool, **kwargs) -> None:
        """Populate related materials from a count or iterable."""
        if not create or extracted is None:
            return
        if isinstance(extracted, int):
            related_materials = [RelatedMaterialFactory() for _ in range(max(extracted, 0))]
        else:
            related_materials = list(extracted)
        self.related_materials.set(related_materials)
