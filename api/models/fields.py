"""Models for common named URI fields used across multiple models."""

from django.db import models

from api.models.base import DefaultColumns


class NamedURI(DefaultColumns):
    """Mixin for models that have a name and a URI."""

    name = models.CharField(max_length=255, unique=True)
    uri = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        """Meta class for NamedURI."""

        abstract = True

    def __str__(self):
        """String representation of the instance."""
        return self.name


class Creator(NamedURI):
    """The creator of the images, image_sets or annotation_sets."""

    class Meta:
        """Meta class for Creator."""

        db_table = "creators"


class Context(NamedURI):
    """The context in which images were captured."""

    class Meta:
        """Meta class for Context."""

        db_table = "contexts"


class Project(NamedURI):
    """The project under which images were captured."""

    class Meta:
        """Meta class for Project."""

        db_table = "projects"


class PI(NamedURI):
    """The principal investigator associated with the images."""

    class Meta:
        """Meta class for PI."""

        db_table = "pis"


class License(NamedURI):
    """The license under which images are made available."""

    class Meta:
        """Meta class for License."""

        db_table = "licenses"
